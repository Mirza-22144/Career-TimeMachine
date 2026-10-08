"""The one live, AI-generated question in a practice activity (Iteration 3,
AC 4.4.6): a scenario about a skill the user typed in herself.

Only the role, the difficulty and skill names are ever sent - never her
name, token, break dates, responsibilities or any job description.
"""

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.providers.ai_pool_v3_scenario_provider import (
    RETRIEVER_BUNDLE_PATH,
    V2_FALLBACK_POOL_PATH,
    V3_POOL_PATH,
    fallback_question,
    question_to_scenario,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LiveQuestion:
    """A question plus the reflective feedback for each of its options.
    The feedback travels with the question because, unlike the static pool,
    there is nowhere to look it up again later."""

    scenario: dict[str, Any]  # ScenarioContent's shape
    option_feedback: dict[str, Any]  # option id -> FeedbackContent's shape
    is_live: bool  # False when this is the static fallback


def _from_question(question: dict[str, Any], is_live: bool) -> LiveQuestion:
    return LiveQuestion(
        scenario=question_to_scenario(question),
        option_feedback=question["option_feedback"],
        is_live=is_live,
    )


def static_fallback(role_id: str, difficulty: str) -> LiveQuestion | None:
    """The AI team's fallback policy: the matching Version 2 question."""
    question = fallback_question(role_id, difficulty)
    return _from_question(question, is_live=False) if question is not None else None


class LiveQuestionProvider(ABC):
    @abstractmethod
    def generate(self, role_id: str, difficulty: str, custom_skills: list[str]) -> LiveQuestion | None:
        """Return a question about one of the custom skills, the static
        fallback if a live one can't be produced, or None if there is
        nothing at all for this role."""
        raise NotImplementedError

    def warm_up(self) -> None:
        """Do any slow one-off setup ahead of the first request."""


class StaticFallbackLiveQuestionProvider(LiveQuestionProvider):
    """Used when live generation isn't configured (no GEMINI_API_KEY) or
    its dependencies aren't installed: always the static fallback."""

    def generate(self, role_id: str, difficulty: str, custom_skills: list[str]) -> LiveQuestion | None:
        return static_fallback(role_id, difficulty)


class GeminiLiveQuestionProvider(LiveQuestionProvider):
    """Wraps the AI team's LiveMCQService (local retrieval + Gemini, with its
    own validation and retry). Built on first use, not at import: it loads
    the MiniLM embedding model, and any failure to build must degrade to
    the static fallback rather than take the app down."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._service: Any | None = None
        self._unavailable = False
        self._lock = threading.Lock()

    def _get_service(self) -> Any | None:
        if self._service is not None or self._unavailable:
            return self._service
        with self._lock:
            if self._service is None and not self._unavailable:
                try:
                    # Heavy imports (sentence-transformers, google-genai) stay
                    # out of module import so tests and a fresh checkout
                    # never need them.
                    from app.ml.reflective_mcq_v3.live_mcq_rag_service import LiveMCQService

                    self._service = LiveMCQService(
                        RETRIEVER_BUNDLE_PATH,
                        V3_POOL_PATH,
                        V2_FALLBACK_POOL_PATH,
                        api_key=self._api_key,
                    )
                except Exception:
                    logger.exception("Live MCQ service could not be started; using the static fallback")
                    self._unavailable = True
        return self._service

    def warm_up(self) -> None:
        # Loading the embedding model takes longer than a request is allowed
        # to wait, so without this the first user after a restart would
        # always get the static fallback.
        self._get_service()

    def generate(self, role_id: str, difficulty: str, custom_skills: list[str]) -> LiveQuestion | None:
        service = self._get_service()
        if service is None:
            return static_fallback(role_id, difficulty)
        try:
            result = service.generate(role_id, difficulty, custom_skills)
        except Exception as exc:
            # Includes a custom skill the service's own input checks reject.
            # Log the type only - never the skill text.
            logger.warning("Live MCQ generation failed (%s); using the static fallback", type(exc).__name__)
            return static_fallback(role_id, difficulty)
        return _from_question(result["question"], is_live=not result["fallback_used"])
