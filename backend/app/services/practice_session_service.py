import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.providers.scenario_provider import (
    ScenarioContent,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)
from app.repositories.interfaces.practice_session_repository import (
    PracticeRoleRef,
    PracticeScenario,
    PracticeSession,
    PracticeSessionRepository,
    ScenarioOption,
)
from app.schemas.practice_session import PracticeSessionCreate
from app.services.practice_role_service import PracticeRoleService

logger = logging.getLogger(__name__)

RequestT = TypeVar("RequestT")

# Provider calls run on worker threads so a slow provider can be abandoned
# after a timeout instead of holding the request open.
_provider_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="scenario-provider")


def call_provider(
    func: Callable[[RequestT], Any],
    request: RequestT,
    timeout_seconds: float,
) -> Any:
    """Run one provider call with a timeout. Every failure, including a
    timeout or an unexpected exception, becomes ScenarioProviderError."""
    future = _provider_executor.submit(func, request)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise ScenarioProviderError("provider timed out") from exc
    except ScenarioProviderError:
        raise
    except Exception as exc:
        raise ScenarioProviderError("provider failed") from exc


def practice_error(status_code: int, code: str, message: str) -> HTTPException:
    """Build a structured error for core/exceptions.py to wrap."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PracticeSessionService:
    """Starts, retrieves and completes workplace-practice sessions."""

    def __init__(
        self,
        sessions: PracticeSessionRepository,
        practice_roles: PracticeRoleService,
        provider: ScenarioProvider,
        provider_timeout_seconds: float = 10.0,
        activity_type: str = "written_response",
    ) -> None:
        # Storage and scenario generation are both behind interfaces, so the
        # database and AI implementations can be swapped in without changes here.
        self.sessions = sessions
        self.practice_roles = practice_roles
        self.provider = provider
        self.provider_timeout_seconds = provider_timeout_seconds
        # The interaction new scenarios use (multiple_choice or written_response).
        self.activity_type = activity_type

    def start_session(self, owner: str, settings: PracticeSessionCreate) -> PracticeSession:
        """Start practice with the saved role, saved career context and the
        chosen settings. Nothing is stored if no scenario can be prepared."""
        context = self.practice_roles.build_practice_context(owner)
        scenario = self._generate_scenario(
            ScenarioRequest(
                role_id=context.role_id,
                role_label=context.role_label,
                years_experience=context.years_experience,
                skills=tuple(context.skills),
                responsibilities=tuple(context.responsibilities),
                duration=settings.duration,
                difficulty=settings.difficulty,
                activity_type=self.activity_type,
            )
        )

        now = utc_now()
        # One active session per user: starting again replaces the old one.
        previous = self.sessions.get_active_for_owner(owner)
        if previous is not None:
            previous.status = "abandoned"
            previous.updated_at = now
            self.sessions.save(previous)

        return self.sessions.add(
            PracticeSession(
                session_id=uuid.uuid4().hex,
                owner_token_hash=owner,
                role=PracticeRoleRef(
                    id=context.role_id,
                    label=context.role_label,
                    source=context.role_source,
                ),
                duration=settings.duration,
                difficulty=settings.difficulty,
                status="active",
                created_at=now,
                updated_at=now,
                scenarios=[scenario],
            )
        )

    def get_session(self, owner: str, session_id: str) -> PracticeSession:
        """Return one of the owner's sessions. Another user's session gets
        the same 404 as a session that does not exist."""
        session = self.sessions.get_for_owner(owner, session_id)
        if session is None:
            raise practice_error(
                status.HTTP_404_NOT_FOUND,
                "PRACTICE_SESSION_NOT_FOUND",
                "Practice session not found",
            )
        return session

    def get_current_session(self, owner: str) -> PracticeSession:
        """Return the owner's active session so practice can be resumed."""
        session = self.sessions.get_active_for_owner(owner)
        if session is None:
            raise practice_error(
                status.HTTP_404_NOT_FOUND,
                "PRACTICE_SESSION_NOT_FOUND",
                "No active practice session",
            )
        return session

    def complete_session(self, owner: str, session_id: str) -> PracticeSession:
        """Mark an active session completed. Completing twice is harmless."""
        session = self.get_session(owner, session_id)
        if session.status == "completed":
            return session
        if session.status != "active":
            raise practice_error(
                status.HTTP_409_CONFLICT,
                "PRACTICE_SESSION_NOT_ACTIVE",
                "Practice session is no longer active",
            )

        now = utc_now()
        session.status = "completed"
        session.completed_at = now
        session.updated_at = now
        return self.sessions.save(session)

    def _generate_scenario(self, request: ScenarioRequest) -> PracticeScenario:
        """Get one scenario of the requested activity type from the provider
        and validate it."""
        try:
            raw = call_provider(
                self.provider.generate_scenario,
                request,
                self.provider_timeout_seconds,
            )
            content = ScenarioContent.model_validate(raw)
            if content.activity_type != request.activity_type:
                raise ScenarioProviderError("provider returned a different activity type")
        except (ScenarioProviderError, ValidationError) as exc:
            # Log the failure type only - never career context or provider output.
            logger.warning("Scenario provider could not supply a scenario (%s)", type(exc).__name__)
            raise practice_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "SCENARIO_UNAVAILABLE",
                "A practice scenario could not be prepared. Please try again.",
            ) from None

        return PracticeScenario(
            **content.model_dump(exclude={"options"}),
            options=[ScenarioOption(option_id=option.option_id, text=option.text) for option in content.options],
            status="current",
        )
