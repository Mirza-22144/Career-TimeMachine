"""Scenario provider backed by the AI team's real generated dataset.

This is Version 1 of the AI team's content: one multiple-choice scenario per
(role, difficulty), 27 roles x 3 difficulties = 81 total (see
app/data/practice_mcq_scenario_pool.json). The dataset's own private answer
key (assessment_reference) has already been stripped out of that file
entirely - this provider never sees which option was "correct" and never
could leak it, by construction.

The AI team has flagged this dataset as graded-format evidence and is
building a reflective-format Version 2 against the agreed contract (no
option marked correct, no score in feedback). Until that lands,
generate_feedback() below synthesises lightweight reflective feedback from
the scenario's own fields (skills_used, new_skill_focus) rather than
inventing a verdict - swap the body of generate_feedback for a real lookup
into Version 2's own feedback content once it is delivered, matching the
same file-loading pattern used in generate_scenario.
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

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "practice_mcq_scenario_pool.json"

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


def _load_scenarios_by_role_difficulty() -> dict[tuple[str, str], dict[str, Any]]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {(q["role_id"], q["difficulty"]): q["scenario"] for q in data["questions"]}


# Loaded once at import time - 81 small JSON scenarios, not worth re-reading
# per request. Swap this whole module for a real HTTP client once the AI
# team exposes an external API, keeping this same (role_id, difficulty) ->
# scenario shape as the contract other code already depends on.
_SCENARIOS_BY_ROLE_DIFFICULTY = _load_scenarios_by_role_difficulty()


class AiPoolScenarioProvider(ScenarioProvider):
    """Serves the AI team's real (role, difficulty) scenario pool."""

    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice":
            raise ScenarioProviderError("The AI pool only has multiple_choice scenarios")

        scenario = _SCENARIOS_BY_ROLE_DIFFICULTY.get((request.role_id, request.difficulty))
        if scenario is None:
            # Not one of the AI pool's 27 roles - most notably the real
            # "other" role (a typed-in previous role with no catalogue
            # entry). Fall back to a generic activity rather than failing
            # the whole session outright.
            content = _generic_scenario(request)
        else:
            content = {
                "scenario_id": scenario["scenario_id"],
                "title": scenario["title"],
                "workplace_area": scenario["workplace_area"],
                "situation": scenario["situation"],
                "task": scenario["task"],
                "activity_type": "multiple_choice",
                "options": scenario["options"],
                "guidance": scenario["guidance"],
                "skills_used": scenario["skills_used"],
                "new_skill_focus": scenario["new_skill_focus"],
            }

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

        skill = request.skills_used[0] if request.skills_used else "this area"
        other_options = [text for text in request.option_texts if text != request.selected_option_text]

        return {
            # References her actual selected option, not just the scenario in
            # general, so feedback genuinely differs by which option she
            # picked (the AI pool's raw option text is all we have per option
            # - there's no curated "why this may help" text to draw on yet).
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
