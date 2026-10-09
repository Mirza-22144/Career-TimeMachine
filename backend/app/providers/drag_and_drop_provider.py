"""Drag and Drop workplace-communication activities (Iteration 3, US 4.6),
from the AI team's handover - vendored into app/ml/drag_and_drop_v1
because the Dockerfile only copies app/.

Static: 324 validated activities, four per (role, difficulty) for 27
roles. Live: when she has typed in a skill of her own, one more is written
by Gemini (LiveDragAndDropService, two attempts, then its own static
fallback).

Each activity is a message with three blanks and five phrases. Three
phrases have a blank they are meant for (fits_blank_id) and two have none.
That mapping stays on the server: the browser only ever gets the phrase
ids and texts, in shuffled order, and never a "correct" label.
"""

import json
import logging
import random
import threading
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DIR = Path(__file__).resolve().parent.parent / "ml" / "drag_and_drop_v1"
POOL_PATH = _DIR / "drag_and_drop_activity_pool_v1_final.json"

BLANK_IDS = ("blank_1", "blank_2", "blank_3")
INSTRUCTION = "Complete the message. Three of the five phrases fit."


def to_scenario(activity_id: str, role_label: str, activity: dict[str, Any]) -> dict[str, Any]:
    """Turn one AI-team activity into the fields of a practice scenario.

    `content` is the server-only part (the template, which blank each
    phrase is meant for, and the feedback for every phrase). The phrases
    are shuffled so their order says nothing about where they go - in the
    source the first three are always the ones that fit, in blank order.
    """
    options = [{"option_id": option["option_id"], "text": option["text"]} for option in activity["options"]]
    random.shuffle(options)
    return {
        "scenario_id": activity_id,
        "title": activity["title"],
        "workplace_area": f"{role_label} Workspace",
        "situation": activity["situation"],
        "task": INSTRUCTION,
        "activity_type": "drag_and_drop",
        "options": options,
        "guidance": list(activity.get("guidance", [])),
        "skills_used": list(activity.get("skills_used", [])),
        "new_skill_focus": None,
        "content": {
            "sentence_template": activity["sentence_template"],
            "fits": {option["option_id"]: option["fits_blank_id"] for option in activity["options"]},
            "feedback_by_option": activity["feedback_by_option"],
        },
    }


class DragDropProvider(ABC):
    """Where Drag and Drop activities come from."""

    @abstractmethod
    def static_activities(self, role_id: str, difficulty: str, exclude: set[str], limit: int) -> list[dict[str, Any]]:
        """Up to `limit` pre-written activities for the role and difficulty
        whose ids are not in `exclude`, as scenario fields (see to_scenario).
        Empty when the role has none or she has done them all."""
        raise NotImplementedError

    @abstractmethod
    def live_activity(
        self,
        role_id: str,
        difficulty: str,
        custom_skills: list[str],
        years_experience: str | None,
        responsibilities: list[str],
    ) -> dict[str, Any] | None:
        """One activity about a skill she typed in herself, or None when it
        cannot be produced."""
        raise NotImplementedError

    def warm_up(self) -> None:
        """Do any slow one-off setup ahead of the first request."""


class AiDragDropProvider(DragDropProvider):
    """The AI team's pool, plus their live service when a Gemini key is set."""

    def __init__(self, api_key: str = "") -> None:
        with open(POOL_PATH, encoding="utf-8") as f:
            records = json.load(f)["activities"]
        self._by_role_difficulty: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for record in sorted(records, key=lambda r: r["activity_id"]):
            self._by_role_difficulty.setdefault((record["role_id"], record["difficulty"]), []).append(record)
        self._api_key = api_key
        self._service: Any | None = None
        self._unavailable = False
        self._lock = threading.Lock()

    def static_activities(self, role_id: str, difficulty: str, exclude: set[str], limit: int) -> list[dict[str, Any]]:
        records = self._by_role_difficulty.get((role_id, difficulty), [])
        return [
            to_scenario(record["activity_id"], record["role_label"], record["activity"])
            for record in records
            if record["activity_id"] not in exclude
        ][:limit]

    def _get_service(self) -> Any | None:
        if self._service is not None or self._unavailable or not self._api_key:
            return self._service
        with self._lock:
            if self._service is None and not self._unavailable:
                try:
                    # google-genai is only imported when a live activity is
                    # first needed, so tests and a fresh checkout never need it.
                    from app.ml.drag_and_drop_v1.live_drag_and_drop_service import LiveDragAndDropService

                    self._service = LiveDragAndDropService(POOL_PATH, api_key=self._api_key)
                except Exception:
                    logger.exception("Live drag-and-drop service could not be started")
                    self._unavailable = True
        return self._service

    def warm_up(self) -> None:
        self._get_service()

    def live_activity(
        self,
        role_id: str,
        difficulty: str,
        custom_skills: list[str],
        years_experience: str | None,
        responsibilities: list[str],
    ) -> dict[str, Any] | None:
        service = self._get_service()
        if service is None or not custom_skills:
            return None
        try:
            result = service.generate(
                {
                    "role_id": role_id,
                    "skills": custom_skills[:8],
                    "years_experience": years_experience,
                    "responsibilities": responsibilities[:10],
                    "difficulty": difficulty,
                    "activity_type": "drag_and_drop",
                }
            )
        except Exception as exc:
            # Includes a role outside the pool and input their checks reject.
            # Log the type only - never her skills or responsibilities.
            logger.warning("Live drag-and-drop generation failed (%s)", type(exc).__name__)
            return None
        if result["source"] != "live_gemini":
            # Their fallback is one of the same pre-written activities this
            # activity is already built from, so it adds nothing.
            return None
        # scenario_id is VARCHAR(64); the longest role ids need trimming.
        activity_id = f"{role_id[:30]}_{difficulty}_dd_live_{uuid.uuid4().hex[:12]}"
        return to_scenario(activity_id, service.role_labels[role_id], result["backend_activity"])
