"""AiPoolScenarioProvider on the Version 2 reflective-format dataset
(app/data/reflective_mcq_scenario_pool_v2.json) - the swap-in described in
BE 2.10's notes. Real per-option feedback should be served when available,
a malformed dataset entry should be dropped (not crash), and the generic
fallback should still work for content outside the pool."""

import logging

from app.providers.ai_pool_scenario_provider import (
    _FEEDBACK_BY_SCENARIO_AND_OPTION,
    _SCENARIOS_BY_ROLE_DIFFICULTY,
    AiPoolScenarioProvider,
)
from app.providers.scenario_provider import (
    FeedbackContent,
    FeedbackRequest,
    ScenarioContent,
    ScenarioRequest,
)

provider = AiPoolScenarioProvider()

KNOWN_BAD_SCENARIO_ID = "computer_network_support_specialist_guided_v2_01"


def _scenario_request(role_id="web_developer", role_label="Web Developer", difficulty="guided", **overrides):
    defaults = dict(
        role_id=role_id,
        role_label=role_label,
        years_experience="5",
        skills=("Python", "React"),
        responsibilities=(),
        duration="10",
        difficulty=difficulty,
        activity_type="multiple_choice",
        exclude_scenario_ids=(),
    )
    return ScenarioRequest(**{**defaults, **overrides})


def test_dataset_loads_almost_all_scenarios():
    # 27 roles x 3 difficulties = 81 in the raw file; one entry has an
    # over-length option and is dropped at load time (see the module's
    # _load_dataset docstring), so 80 remain servable.
    assert len(_SCENARIOS_BY_ROLE_DIFFICULTY) == 80


def test_known_bad_entry_is_dropped_not_served():
    served_ids = {v["scenario_id"] for v in _SCENARIOS_BY_ROLE_DIFFICULTY.values()}
    assert KNOWN_BAD_SCENARIO_ID not in served_ids

    key = ("computer_network_support_specialist", "guided")
    assert key not in _SCENARIOS_BY_ROLE_DIFFICULTY

    # Requesting it falls through to the generic fallback rather than
    # raising or returning nothing.
    scenario = provider.generate_scenario(
        _scenario_request(role_id="computer_network_support_specialist", difficulty="guided")
    )
    assert scenario["scenario_id"] == "generic_computer_network_support_specialist_guided"


def test_dropped_entry_logged_a_warning(caplog):
    # The drop happens at import time (module load), so re-run the loader
    # directly to observe the log for this one entry.
    with caplog.at_level(logging.WARNING):
        from app.providers.ai_pool_scenario_provider import _load_dataset

        _load_dataset()

    warnings = [r.getMessage() for r in caplog.records if r.name == "app.providers.ai_pool_scenario_provider"]
    assert any(KNOWN_BAD_SCENARIO_ID in message for message in warnings)


def test_every_loaded_scenario_and_its_feedback_is_valid():
    for scenario in _SCENARIOS_BY_ROLE_DIFFICULTY.values():
        ScenarioContent.model_validate(scenario)
    for feedback in _FEEDBACK_BY_SCENARIO_AND_OPTION.values():
        FeedbackContent.model_validate(feedback)


def test_real_scenario_uses_authored_feedback_and_varies_by_option():
    scenario = provider.generate_scenario(_scenario_request())
    assert len(scenario["options"]) >= 2

    feedback_by_option = {}
    for option in scenario["options"]:
        request = FeedbackRequest(
            role_label="Web Developer",
            difficulty="guided",
            scenario_id=scenario["scenario_id"],
            situation=scenario["situation"],
            task=scenario["task"],
            skills_used=scenario["skills_used"],
            new_skill_focus=scenario["new_skill_focus"],
            activity_type="multiple_choice",
            selected_option_id=option["option_id"],
            selected_option_text=option["text"],
            option_texts=tuple(o["text"] for o in scenario["options"]),
        )
        feedback_by_option[option["option_id"]] = provider.generate_feedback(request)

    # Real authored feedback, so the content genuinely differs per option,
    # not just a template with the option text substituted in.
    bodies = {tuple(fb["what_worked_well"]) for fb in feedback_by_option.values()}
    assert len(bodies) == len(feedback_by_option)


def test_generic_fallback_still_used_for_role_outside_the_pool():
    scenario = provider.generate_scenario(_scenario_request(role_id="other", role_label="Freelance Juggler"))
    assert scenario["scenario_id"] == "generic_other_guided"

    feedback = provider.generate_feedback(
        FeedbackRequest(
            role_label="Freelance Juggler",
            difficulty="guided",
            scenario_id=scenario["scenario_id"],
            situation=scenario["situation"],
            task=scenario["task"],
            skills_used=scenario["skills_used"],
            new_skill_focus=scenario["new_skill_focus"],
            activity_type="multiple_choice",
            selected_option_id=scenario["options"][0]["option_id"],
            selected_option_text=scenario["options"][0]["text"],
            option_texts=tuple(o["text"] for o in scenario["options"]),
        )
    )
    FeedbackContent.model_validate(feedback)
