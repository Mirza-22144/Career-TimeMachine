"""Practice-session repository behaviour for multiple-choice data: options,
the selected option and feedback round-trip, copies are isolated and reads
stay scoped to the owner. The database implementation must behave the same."""

from datetime import datetime, timezone

from app.repositories.interfaces.practice_session_repository import (
    PracticeRoleRef,
    PracticeScenario,
    PracticeSession,
    ReflectiveFeedback,
    ScenarioAttempt,
    ScenarioOption,
    SuggestedSkill,
)
from app.repositories.memory.memory_practice_session_repository import (
    MemoryPracticeSessionRepository,
)

NOW = datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)
OWNER = "owner-hash"


def _session() -> PracticeSession:
    return PracticeSession(
        session_id="session-1",
        owner_token_hash=OWNER,
        role=PracticeRoleRef(id="software_engineer", label="Software Engineer", source="previous"),
        duration="quick",
        difficulty="standard",
        status="active",
        created_at=NOW,
        updated_at=NOW,
        scenarios=[
            PracticeScenario(
                scenario_id="software_slow_release",
                title="Slow responses after a release",
                workplace_area="Engineering team desk",
                situation="A release slowed down the order history page.",
                task="What would you do first to investigate the slowdown?",
                activity_type="multiple_choice",
                guidance=[],
                skills_used=["Debugging"],
                new_skill_focus="Observability",
                options=[
                    ScenarioOption("software_slow_release_a", "Compare the release with monitoring data"),
                    ScenarioOption("software_slow_release_b", "Roll back the release"),
                ],
            )
        ],
    )


def test_selected_option_and_feedback_are_saved_and_retrieved():
    repository = MemoryPracticeSessionRepository()
    session = repository.add(_session())
    scenario = session.scenarios[0]
    scenario.status = "completed"
    scenario.response = ScenarioAttempt(submitted_at=NOW, selected_option_id="software_slow_release_b")
    scenario.feedback = ReflectiveFeedback(
        what_worked_well=["Rolling back can restore service quickly."],
        areas_to_consider=["How would you confirm the rollback helped?"],
        skill_to_explore=SuggestedSkill("Observability", "It shows where time is spent."),
        trade_offs=["A rollback also removes fixes in the release."],
    )
    scenario.feedback_status = "available"
    repository.save(session)

    stored = repository.get_for_owner(OWNER, "session-1")

    assert stored == session
    assert stored.scenarios[0].response.selected_option_id == "software_slow_release_b"
    assert stored.scenarios[0].response.response_text is None
    assert stored.scenarios[0].feedback.trade_offs == ["A rollback also removes fixes in the release."]
    assert [option.option_id for option in stored.scenarios[0].options] == [
        "software_slow_release_a",
        "software_slow_release_b",
    ]
    assert stored.progress.completed_activities == 1
    assert stored.progress.current_scenario_id is None


def test_unsaved_changes_to_options_or_answers_do_not_reach_the_store():
    repository = MemoryPracticeSessionRepository()
    repository.add(_session())

    loaded = repository.get_for_owner(OWNER, "session-1")
    loaded.scenarios[0].options.append(ScenarioOption("injected", "Injected option"))
    loaded.scenarios[0].response = ScenarioAttempt(submitted_at=NOW, selected_option_id="injected")

    stored = repository.get_for_owner(OWNER, "session-1")
    assert len(stored.scenarios[0].options) == 2
    assert stored.scenarios[0].response is None


def test_another_owner_cannot_read_the_session_or_its_choice():
    repository = MemoryPracticeSessionRepository()
    repository.add(_session())

    assert repository.get_for_owner("other-hash", "session-1") is None
    assert repository.get_active_for_owner("other-hash") is None
