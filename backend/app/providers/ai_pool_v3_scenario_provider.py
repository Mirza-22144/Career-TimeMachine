"""Scenario provider backed by the AI team's Version 3 reflective MCQ pool
(Iteration 3, backend/ai/reflective_mcq_v3 - vendored into
app/ml/reflective_mcq_v3 because the Dockerfile only copies app/).

Version 3: four multiple-choice scenarios per (role, difficulty), 27 roles x
3 difficulties = 324. Reflective by design - no option is marked correct and
every option carries its own authored feedback, so generate_feedback() is a
lookup, not a synthesis. A role outside the 27 (most notably "other", a
typed-in previous role) falls through to the Version 2 provider's generic
activity, exactly as before.
"""

import json
from pathlib import Path
from typing import Any

from app.providers.ai_pool_scenario_provider import AiPoolScenarioProvider, _title_case
from app.providers.scenario_provider import (
    FeedbackRequest,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)

_POOL_DIR = Path(__file__).resolve().parent.parent / "ml" / "reflective_mcq_v3"
V3_POOL_PATH = _POOL_DIR / "reflective_mcq_scenario_pool_v3_final.json"
V2_FALLBACK_POOL_PATH = _POOL_DIR / "reflective_mcq_scenario_pool_v2_fallback.json"
RETRIEVER_BUNDLE_PATH = _POOL_DIR / "live_mcq_hybrid_semantic_retriever_v2_2.joblib"


def question_to_scenario(question: dict[str, Any]) -> dict[str, Any]:
    """Turn one AI-team question record (static, fallback or live - they
    share a shape) into ScenarioContent's shape."""
    body = question["question"]
    title_source = question["target_skills"][:2] or [question["role_label"]]
    return {
        "scenario_id": question["question_id"],
        "title": " & ".join(_title_case(skill) for skill in title_source),
        "workplace_area": f"{question['role_label']} Workspace",
        "situation": body["situation"],
        "task": body["task"],
        "activity_type": "multiple_choice",
        "options": [{"option_id": option["id"], "text": option["text"]} for option in body["options"]],
        "guidance": list(body["hints"]),
        "skills_used": [_title_case(skill) for skill in question["target_skills"]],
        "new_skill_focus": None,
    }


def _load(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["questions"]


# Loaded once at import time - 405 small JSON records.
_V3_QUESTIONS = _load(V3_POOL_PATH)
_V2_FALLBACK_QUESTIONS = _load(V2_FALLBACK_POOL_PATH)

_V3_BY_ROLE_DIFFICULTY: dict[tuple[str, str], list[dict[str, Any]]] = {}
for _question in sorted(_V3_QUESTIONS, key=lambda q: q["question_id"]):
    _V3_BY_ROLE_DIFFICULTY.setdefault((_question["role_id"], _question["difficulty"]), []).append(
        question_to_scenario(_question)
    )

_FALLBACK_BY_ROLE_DIFFICULTY = {(q["role_id"], q["difficulty"]): q for q in _V2_FALLBACK_QUESTIONS}

_OPTION_FEEDBACK_BY_SCENARIO = {
    q["question_id"]: q["option_feedback"] for q in [*_V2_FALLBACK_QUESTIONS, *_V3_QUESTIONS]
}


def fallback_question(role_id: str, difficulty: str) -> dict[str, Any] | None:
    """The Version 2 question used in place of a live one that could not be
    generated (AI team's fallback policy), or None for a role outside the pool."""
    return _FALLBACK_BY_ROLE_DIFFICULTY.get((role_id, difficulty))


class AiPoolV3ScenarioProvider(ScenarioProvider):
    """Serves the Version 3 pool: up to four scenarios per (role, difficulty),
    handed out one at a time through exclude_scenario_ids."""

    def __init__(self) -> None:
        # Generic activity + feedback for roles the pool doesn't cover.
        self._v2 = AiPoolScenarioProvider()

    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice":
            raise ScenarioProviderError("The AI pool only has multiple_choice scenarios")

        pool = _V3_BY_ROLE_DIFFICULTY.get((request.role_id, request.difficulty))
        if pool is None:
            return self._v2.generate_scenario(request)

        for scenario in pool:
            if scenario["scenario_id"] not in request.exclude_scenario_ids:
                return scenario
        raise ScenarioProviderError("No further scenarios for this role and difficulty")

    def skills_for_role(self, role_id: str) -> list[str]:
        return sorted(
            {
                skill
                for (pool_role_id, _difficulty), scenarios in _V3_BY_ROLE_DIFFICULTY.items()
                if pool_role_id == role_id
                for scenario in scenarios
                for skill in scenario["skills_used"]
            }
        )

    def generate_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice" or request.selected_option_id is None:
            raise ScenarioProviderError("The AI pool only has multiple_choice feedback")

        authored = _OPTION_FEEDBACK_BY_SCENARIO.get(request.scenario_id)
        if authored is None:
            return self._v2.generate_feedback(request)
        feedback = authored.get(request.selected_option_id)
        if feedback is None:
            raise ScenarioProviderError("No feedback authored for this option")
        return feedback
