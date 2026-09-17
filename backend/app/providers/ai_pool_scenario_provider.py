"""Scenario provider backed by the AI team's real reflective MCQ dataset.

Version 2: one multiple-choice scenario per (role, difficulty), 27 roles x 3
difficulties = 81 total (see app/data/reflective_mcq_scenario_pool_v2.json).
Reflective by design: no option is marked correct, and every option carries
its own authored feedback (what worked well, trade-offs, areas to consider,
skill to explore) rather than one shared verdict per scenario - so
generate_feedback() below is a real lookup into the dataset, not a synthesis.
"""

import json
from pathlib import Path
from typing import Any

from app.providers.scenario_provider import (
    FeedbackRequest,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "reflective_mcq_scenario_pool_v2.json"

# Same three hints, sliced per difficulty (all for guided, one for standard,
# none for challenge - the documented contract in API-CONTRACT.md). Used
# only as a fallback for a role_id outside the AI pool's 27 roles - most
# notably the real "other" role (a user's typed-in previous role, which the
# AI pool has no content for since it isn't one of the 27 catalogue roles).
_GENERIC_GUIDANCE = (
    "Think about what's actually being asked before jumping to a solution.",
    "Consider how this would play out for someone relying on your work.",
    "There's often more than one reasonable approach - weigh the trade-offs.",
)
_HINT_COUNT_BY_DIFFICULTY = {"guided": 3, "standard": 1, "challenge": 0}


def _title_case(phrase: str) -> str:
    """Capitalise each word, leaving an already-uppercase word (an acronym
    like SQL) alone."""
    return " ".join(word if word.isupper() else word.capitalize() for word in phrase.split())


def _generic_scenario(request: ScenarioRequest) -> dict[str, Any]:
    label = request.role_label or request.role_id.replace("_", " ").title()
    hint_count = _HINT_COUNT_BY_DIFFICULTY.get(request.difficulty, 0)

    # Her own skills first (personalises the fallback, matching the curated
    # provider's technique), then generic ones, capped at a sensible length.
    skills_used = list(request.skills[:2])
    for skill in ("Communication", "Prioritisation"):
        if skill.lower() not in {s.lower() for s in skills_used}:
            skills_used.append(skill)

    return {
        "scenario_id": f"generic_{request.role_id}_{request.difficulty}",
        "title": "A New Priority Comes In",
        "workplace_area": f"{label} Desk",
        "situation": "A colleague needs your help with an unexpected, time-sensitive request.",
        "task": f"How would you prioritise this against your existing work as a {label.lower()}?",
        "activity_type": "multiple_choice",
        "options": [
            {"option_id": "generic_a", "text": "Ask what's driving the urgency before deciding how to fit it in."},
            {"option_id": "generic_b", "text": "Drop what you're doing and start on it immediately."},
            {"option_id": "generic_c", "text": "Tell them it will have to wait until your current work is done."},
        ],
        "guidance": list(_GENERIC_GUIDANCE[:hint_count]),
        "skills_used": skills_used,
        "new_skill_focus": "Prioritisation under pressure",
    }


def _generic_feedback(request: FeedbackRequest) -> dict[str, Any]:
    """Synthesised feedback for the generic fallback scenario, which has no
    authored per-option content of its own to look up."""
    skill = request.skills_used[0] if request.skills_used else "this area"
    other_options = [text for text in request.option_texts if text != request.selected_option_text]

    return {
        "what_worked_well": [
            f"Choosing “{request.selected_option_text}” draws on {skill.lower()}, which is "
            f"already part of your experience as a {request.role_label.lower()}."
        ],
        "trade_offs": [
            f"“{request.selected_option_text}” is a reasonable approach here, but it isn't "
            "the only one - the right trade-off can depend on timing and context."
        ],
        "areas_to_consider": (
            [
                f"Think through what “{other_options[0]}” would look like in practice, and "
                "when you might reach for it instead."
            ]
            if other_options
            else ["Think through what else might have been a reasonable approach here."]
        ),
        "skill_to_explore": (
            {
                "skill": request.new_skill_focus,
                "why_relevant": f"{request.new_skill_focus} builds directly on what this activity covered.",
            }
            if request.new_skill_focus
            else None
        ),
    }


def _load_dataset() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios: dict[tuple[str, str], dict[str, Any]] = {}
    feedback_by_scenario: dict[str, dict[str, Any]] = {}

    for q in data["questions"]:
        question = q["question"]
        scenario_id = q["question_id"]
        title_source = q["target_skills"][:2] or [q["role_label"]]

        scenarios[(q["role_id"], q["difficulty"])] = {
            "scenario_id": scenario_id,
            "title": " & ".join(_title_case(skill) for skill in title_source),
            "workplace_area": f"{q['role_label']} Workspace",
            "situation": question["situation"],
            "task": question["task"],
            "activity_type": "multiple_choice",
            "options": [{"option_id": o["id"], "text": o["text"]} for o in question["options"]],
            "guidance": list(question["hints"]),
            "skills_used": [_title_case(skill) for skill in q["target_skills"]],
            "new_skill_focus": None,
        }
        feedback_by_scenario[scenario_id] = q["option_feedback"]

    return scenarios, feedback_by_scenario


# Loaded once at import time - 81 small JSON scenarios, not worth re-reading
# per request. Swap this whole module for a real HTTP client once the AI
# team exposes an external API, keeping this same (role_id, difficulty) ->
# scenario shape as the contract other code already depends on.
_SCENARIOS_BY_ROLE_DIFFICULTY, _OPTION_FEEDBACK_BY_SCENARIO = _load_dataset()


class AiPoolScenarioProvider(ScenarioProvider):
    """Serves the AI team's real (role, difficulty) reflective scenario pool."""

    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice":
            raise ScenarioProviderError("The AI pool only has multiple_choice scenarios")

        content = _SCENARIOS_BY_ROLE_DIFFICULTY.get((request.role_id, request.difficulty))
        if content is None:
            # Not one of the AI pool's 27 roles - most notably the real
            # "other" role (a typed-in previous role with no catalogue
            # entry). Fall back to a generic activity rather than failing
            # the whole session outright.
            content = _generic_scenario(request)

        if content["scenario_id"] in request.exclude_scenario_ids:
            # There is exactly one scenario per (role, difficulty) in this
            # pool (and the generic fallback is likewise a single fixed
            # activity), so once it has been served there is nothing
            # further to offer for this exact combination.
            raise ScenarioProviderError("No further AI-pool scenarios for this role and difficulty")

        return content

    def generate_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice" or request.selected_option_id is None:
            raise ScenarioProviderError("The AI pool only has multiple_choice feedback")

        authored = _OPTION_FEEDBACK_BY_SCENARIO.get(request.scenario_id)
        if authored is not None:
            feedback = authored.get(request.selected_option_id)
            if feedback is None:
                raise ScenarioProviderError("No feedback authored for this option")
            return feedback

        # Not one of the AI pool's 81 scenarios - the generic fallback,
        # which has no authored feedback of its own to look up.
        return _generic_feedback(request)
