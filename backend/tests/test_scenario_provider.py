"""Scenario-provider contract and the curated development provider
(backend Subtask 7)."""

import builtins

import pytest
from pydantic import ValidationError

from app.providers.curated_scenario_provider import (
    CURATED_SCENARIOS,
    CuratedScenarioProvider,
    role_family,
)
from app.providers.scenario_provider import (
    FeedbackContent,
    FeedbackRequest,
    ScenarioContent,
    ScenarioProviderError,
    ScenarioRequest,
)

provider = CuratedScenarioProvider()

REPRESENTATIVE_ROLES = {
    "software": "software_developer",
    "data": "data_scientist",
    "quality": "qa_engineer",
    "security": "penetration_tester",
    "infrastructure": "network_and_systems_administrator",
    "general": "other",
}


def _request(role_id="software_developer", difficulty="standard", **overrides) -> ScenarioRequest:
    values = {
        "role_id": role_id,
        "role_label": "Software Developer",
        "years_experience": "5 years",
        "skills": ("Python", "Git"),
        "responsibilities": ("API design",),
        "duration": "standard",
        "difficulty": difficulty,
        "activity_type": "written_response",
    }
    values.update(overrides)
    return ScenarioRequest(**values)


def _feedback_request(scenario: ScenarioContent, response_text: str) -> FeedbackRequest:
    return FeedbackRequest(
        role_label="Software Developer",
        difficulty="standard",
        scenario_id=scenario.scenario_id,
        situation=scenario.situation,
        task=scenario.task,
        skills_used=tuple(scenario.skills_used),
        new_skill_focus=scenario.new_skill_focus,
        activity_type=scenario.activity_type,
        response_text=response_text,
    )


@pytest.mark.parametrize(
    ("role_id", "family"),
    [
        ("software_developer", "software"),
        ("web_developer", "software"),
        ("information_security_engineer", "security"),
        ("data_scientist", "data"),
        ("database_administrator", "data"),
        ("software_quality_assurance_analyst", "quality"),
        ("qa_engineer", "quality"),
        ("computer_network_support_specialist", "infrastructure"),
        ("it_project_manager", "general"),
        ("other", "general"),
    ],
)
def test_roles_map_to_a_scenario_family(role_id, family):
    assert role_family(role_id) == family


@pytest.mark.parametrize("family", sorted(CURATED_SCENARIOS))
@pytest.mark.parametrize("difficulty", ["guided", "standard", "challenge"])
def test_every_curated_scenario_passes_the_provider_contract(family, difficulty):
    for scenario in CURATED_SCENARIOS[family]:
        exclude = tuple(s.scenario_id for s in CURATED_SCENARIOS[family] if s is not scenario)
        role_id = REPRESENTATIVE_ROLES[family]

        content = ScenarioContent.model_validate(
            provider.generate_scenario(
                _request(role_id=role_id, difficulty=difficulty, exclude_scenario_ids=exclude)
            )
        )
        feedback = FeedbackContent.model_validate(
            provider.generate_feedback(_feedback_request(content, "I would start by asking questions."))
        )

        assert content.scenario_id == scenario.scenario_id
        assert feedback.skill_to_explore is not None


def test_difficulty_changes_the_guidance_offered():
    guided = provider.generate_scenario(_request(difficulty="guided"))
    standard = provider.generate_scenario(_request(difficulty="standard"))
    challenge = provider.generate_scenario(_request(difficulty="challenge"))

    assert len(guided["guidance"]) == 3
    assert len(standard["guidance"]) == 1
    assert challenge["guidance"] == []
    assert challenge["task"].endswith("Note any assumptions you are making.")


def test_scenario_includes_the_users_saved_skills():
    scenario = provider.generate_scenario(_request(skills=("Python", "Git", "Docker")))

    assert scenario["skills_used"][-2:] == ["Python", "Git"]


def test_excluded_scenarios_are_skipped_until_none_remain():
    first = provider.generate_scenario(_request())
    second = provider.generate_scenario(_request(exclude_scenario_ids=(first["scenario_id"],)))

    assert second["scenario_id"] != first["scenario_id"]
    with pytest.raises(ScenarioProviderError):
        provider.generate_scenario(
            _request(exclude_scenario_ids=(first["scenario_id"], second["scenario_id"]))
        )


def test_feedback_reflects_on_the_response_without_judging_it():
    scenario = ScenarioContent.model_validate(provider.generate_scenario(_request()))
    detailed = " ".join(["I would check the monitoring dashboards and use my Debugging experience."] * 8)

    short_feedback = provider.generate_feedback(_feedback_request(scenario, "Roll it back."))
    detailed_feedback = provider.generate_feedback(_feedback_request(scenario, detailed))

    assert len(detailed_feedback["what_worked_well"]) > len(short_feedback["what_worked_well"])
    assert len(short_feedback["areas_to_consider"]) > len(detailed_feedback["areas_to_consider"])
    assert set(detailed_feedback) == {"what_worked_well", "areas_to_consider", "skill_to_explore"}


def test_feedback_for_an_unknown_scenario_is_a_provider_error():
    scenario = ScenarioContent.model_validate(provider.generate_scenario(_request()))
    unknown = scenario.model_copy(update={"scenario_id": "not_curated"})

    with pytest.raises(ScenarioProviderError):
        provider.generate_feedback(_feedback_request(unknown, "Anything"))


def test_submitted_code_is_treated_as_text_and_never_executed():
    scenario = ScenarioContent.model_validate(provider.generate_scenario(_request()))
    code = "import builtins\nbuiltins.ctm_code_was_executed = True\n"

    feedback = provider.generate_feedback(_feedback_request(scenario, code))

    FeedbackContent.model_validate(feedback)
    assert not hasattr(builtins, "ctm_code_was_executed")


VALID_FEEDBACK = {
    "what_worked_well": ["You asked clarifying questions early."],
    "areas_to_consider": ["How would you share progress with support?"],
    "skill_to_explore": {"skill": "Observability", "why_relevant": "It shows where time is spent."},
}


@pytest.mark.parametrize(
    "change",
    [
        {"score": 7},
        {"passed": True},
        {"what_worked_well": ["You scored 7/10 on this task."]},
        {"what_worked_well": ["You passed this activity."]},
        {"areas_to_consider": ["That answer was 80% complete."]},
        {"areas_to_consider": ["You are not employable yet."]},
        {"what_worked_well": []},
        {"areas_to_consider": ["x" * 501]},
    ],
)
def test_feedback_contract_rejects_scores_judgements_and_bad_shapes(change):
    with pytest.raises(ValidationError):
        FeedbackContent.model_validate({**VALID_FEEDBACK, **change})


def test_feedback_contract_allows_ordinary_workplace_wording():
    feedback = FeedbackContent.model_validate(
        {
            **VALID_FEEDBACK,
            "what_worked_well": ["You thought about passing request IDs between services."],
        }
    )

    assert feedback.what_worked_well == ["You thought about passing request IDs between services."]


@pytest.mark.parametrize(
    "change",
    [
        {"task": ""},
        {"situation": "x" * 2001},
        {"activity_type": "execute_code"},
        {"scenario_id": "Has Spaces"},
        {"difficulty_score": 3},
    ],
)
def test_scenario_contract_rejects_invalid_provider_output(change):
    valid = provider.generate_scenario(_request())

    with pytest.raises(ValidationError):
        ScenarioContent.model_validate({**valid, **change})
