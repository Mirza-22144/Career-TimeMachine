"""Scenario provider backed by the AI team's real generated dataset.

This is Version 2 of the AI team's content (see
app/data/reflective_mcq_scenario_pool_v2.json): one multiple-choice scenario
per (role, difficulty), 27 roles x 3 difficulties = 81 total, each with real
per-option reflective feedback authored against the agreed contract - no
option marked correct, no score anywhere in the file. Version 1
(app/data/practice_mcq_scenario_pool.json) is graded-format evidence only and
is no longer loaded; it is kept on disk for reference.

Every scenario and every one of its four options' feedback is validated
against the real ScenarioContent/FeedbackContent Pydantic models at import
time, exactly like the rest of this codebase validates provider output
before it reaches a user. An entry that fails validation (a delivered
dataset is external input, not code this team wrote) is logged and dropped
rather than crashing the app - generate_scenario() then falls through to the
same generic fallback already used for a role outside the pool, so one bad
row degrades gracefully instead of taking down every session for that role.
"""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.providers.scenario_provider import (
    FeedbackContent,
    FeedbackRequest,
    ScenarioContent,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)

logger = logging.getLogger(__name__)

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


def _scenario_dict(question: dict[str, Any]) -> dict[str, Any]:
    body = question["question"]
    role_label = question["role_label"]
    target_skills = question["target_skills"]

    return {
        "scenario_id": question["question_id"],
        "title": f"{role_label} — {question['difficulty'].title()} Scenario",
        "workplace_area": role_label,
        "situation": body["situation"],
        "task": body["task"],
        "activity_type": "multiple_choice",
        "options": [{"option_id": o["id"], "text": o["text"]} for o in body["options"]],
        "guidance": body.get("hints") or [],
        "skills_used": target_skills,
        "new_skill_focus": target_skills[0] if target_skills else None,
    }


def _feedback_dict(raw: dict[str, Any]) -> dict[str, Any]:
    skill_to_explore = raw.get("skill_to_explore")
    return {
        "what_worked_well": raw["what_worked_well"],
        "trade_offs": raw.get("trade_offs", []),
        "areas_to_consider": raw["areas_to_consider"],
        "skill_to_explore": (
            {
                "skill": skill_to_explore["skill"],
                "why_relevant": skill_to_explore.get("why_relevant") or skill_to_explore["skill"],
            }
            if skill_to_explore
            else None
        ),
    }


def _load_dataset() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    """Return (scenarios_by_role_difficulty, feedback_by_scenario_and_option).

    Only entries that pass the real ScenarioContent/FeedbackContent
    validation are kept - see the module docstring. A scenario is only kept
    if all of its own options' feedback also validates, so a session can
    never reach an option with no valid feedback behind it.
    """
    with open(_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios: dict[tuple[str, str], dict[str, Any]] = {}
    feedback: dict[tuple[str, str], dict[str, Any]] = {}

    for question in data["questions"]:
        scenario_id = question["question_id"]
        key = (question["role_id"], question["difficulty"])

        try:
            scenario_content = _scenario_dict(question)
            ScenarioContent.model_validate(scenario_content)

            option_feedback = {
                option_id: _feedback_dict(raw) for option_id, raw in question["option_feedback"].items()
            }
            for option_id, feedback_content in option_feedback.items():
                FeedbackContent.model_validate(feedback_content)
        except (ValidationError, KeyError) as exc:
            logger.warning(
                "Dropping invalid reflective-MCQ dataset entry scenario_id=%s: %s",
                scenario_id,
                exc,
            )
            continue

        scenarios[key] = scenario_content
        for option_id, feedback_content in option_feedback.items():
            feedback[(scenario_id, option_id)] = feedback_content

    return scenarios, feedback


# Loaded once at import time - 81 small JSON scenarios, not worth re-reading
# per request. Swap this whole module for a real HTTP client once the AI
# team exposes an external API, keeping this same (role_id, difficulty) ->
# scenario shape as the contract other code already depends on.
_SCENARIOS_BY_ROLE_DIFFICULTY, _FEEDBACK_BY_SCENARIO_AND_OPTION = _load_dataset()


class AiPoolScenarioProvider(ScenarioProvider):
    """Serves the AI team's real (role, difficulty) scenario pool."""

    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        if request.activity_type != "multiple_choice":
            raise ScenarioProviderError("The AI pool only has multiple_choice scenarios")

        scenario = _SCENARIOS_BY_ROLE_DIFFICULTY.get((request.role_id, request.difficulty))
        if scenario is None:
            # Not one of the AI pool's 27 roles, or the one dropped at load
            # time for failing validation - most notably also covers the
            # real "other" role (a typed-in previous role with no catalogue
            # entry). Fall back to a generic activity rather than failing
            # the whole session outright.
            content = _generic_scenario(request)
        else:
            content = dict(scenario)

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

        authored = _FEEDBACK_BY_SCENARIO_AND_OPTION.get((request.scenario_id, request.selected_option_id))
        if authored is not None:
            # Real feedback the AI team wrote for this exact option -
            # already validated at load time.
            return dict(authored)

        # No authored feedback for this (scenario, option) - either the
        # scenario came from the generic fallback, or its dataset entry was
        # dropped at load time. Synthesise lightweight reflective feedback
        # from the scenario's own fields instead of failing the request.
        skill = request.skills_used[0] if request.skills_used else "this area"
        other_options = [text for text in request.option_texts if text != request.selected_option_text]

        return {
            # References her actual selected option, not just the scenario in
            # general, so feedback genuinely differs by which option she
            # picked.
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
