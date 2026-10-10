"""Code Review workplace activities (Iteration 3, US 4.7), from the AI
team's static handover (backend/ai/code_review_v1) - the pool is vendored
into app/ml/code_review_v1 because the Dockerfile only copies app/.

324 validated activities: four per (role, difficulty) for 27 roles. Each is
a workplace situation, a short piece of code that is shown read-only and
never run, and four options describing the kind of issue it may have.

Static only: no Gemini, no API key. Which option the authors had in mind
(correct_option_id) and the feedback for every option stay on the server;
the browser gets the feedback for the option she chose, after she submits,
and never a right/wrong label.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

POOL_PATH = Path(__file__).resolve().parent.parent / "ml" / "code_review_v1" / "code_review_activity_pool_v1_final.json"

TASK = "What kind of issue does this code have?"


def scenario_id_for(question_id: str) -> str:
    """The pool's ids run to 71 characters for the longest role ids, and
    practice_scenario.scenario_id is VARCHAR(64). Shortening the fixed
    middle part keeps every id unique and inside the column."""
    return question_id.replace("_code_review_v1_", "_cr_v1_")


def to_scenario(record: dict[str, Any]) -> dict[str, Any]:
    """Turn one AI-team record into the fields of a practice scenario.
    `content` is the server-only part."""
    return {
        "scenario_id": scenario_id_for(record["question_id"]),
        "title": record["title"],
        "workplace_area": f"{record['role_label']} Workspace",
        "situation": record["situation"],
        "task": TASK,
        "activity_type": "code_review",
        "options": [{"option_id": option["option_id"], "text": option["text"]} for option in record["options"]],
        "guidance": list(record.get("guidance", [])),
        "skills_used": list(record.get("skills_used", [])),
        "new_skill_focus": None,
        "content": {
            "language": record["language"],
            "code_snippet": record["code_snippet"],
            "correct_option_id": record["correct_option_id"],
            "option_feedback": {entry["option_id"]: entry["feedback"] for entry in record["option_feedback"]},
        },
    }


class CodeReviewProvider(ABC):
    """Where Code Review activities come from."""

    @abstractmethod
    def static_activities(self, role_id: str, difficulty: str, exclude: set[str], limit: int) -> list[dict[str, Any]]:
        """Up to `limit` activities for the role and difficulty whose
        scenario ids are not in `exclude`, as scenario fields (see
        to_scenario). Empty when the role has none or she has done them all."""
        raise NotImplementedError


class AiCodeReviewProvider(CodeReviewProvider):
    """The AI team's static pool."""

    def __init__(self) -> None:
        with open(POOL_PATH, encoding="utf-8") as f:
            records = json.load(f)["activities"]
        self._by_role_difficulty: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for record in sorted(records, key=lambda r: r["question_id"]):
            self._by_role_difficulty.setdefault((record["role_id"], record["difficulty"]), []).append(record)

    def static_activities(self, role_id: str, difficulty: str, exclude: set[str], limit: int) -> list[dict[str, Any]]:
        records = self._by_role_difficulty.get((role_id, difficulty), [])
        return [
            to_scenario(record) for record in records if scenario_id_for(record["question_id"]) not in exclude
        ][:limit]
