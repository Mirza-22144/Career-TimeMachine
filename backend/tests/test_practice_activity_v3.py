"""Iteration 3 practice activity: four pre-written questions served one at a
time, plus one live question when she typed in a skill of her own."""

from fastapi.testclient import TestClient

from app.main import app
from app.providers.live_question_provider import LiveQuestion, LiveQuestionProvider

client = TestClient(app)

SETTINGS = {"duration": "standard", "difficulty": "guided"}
ROLE = "web_developer"  # in both the test catalogue and the real question pool


class FakeLive(LiveQuestionProvider):
    def __init__(self):
        self.calls = []

    def generate(self, role_id, difficulty, custom_skills):
        self.calls.append((role_id, difficulty, list(custom_skills)))
        feedback = {
            "what_worked_well": ["You weighed the options."],
            "trade_offs": ["It takes longer."],
            "areas_to_consider": ["Who else is affected."],
            "skill_to_explore": {"skill": "Looker", "why_relevant": "It builds on this."},
        }
        return LiveQuestion(
            scenario={
                "scenario_id": "web_developer_guided_live_v3_test",
                "title": "Looker",
                "workplace_area": "Web Developer Workspace",
                "situation": "A dashboard is slow.",
                "task": "What do you do first?",
                "activity_type": "multiple_choice",
                "options": [{"option_id": "a", "text": "Profile it."}, {"option_id": "b", "text": "Ask the team."}],
                "guidance": [],
                "skills_used": ["Looker"],
                "new_skill_focus": None,
            },
            option_feedback={"a": feedback, "b": feedback},
            is_live=True,
        )


class BrokenLive(LiveQuestionProvider):
    def generate(self, role_id, difficulty, custom_skills):
        raise RuntimeError("generator is down")


def _ready(custom_skills=()):
    token = client.post("/api/v1/anonymous-sessions").json()["token"]
    headers = {"X-Session-Token": token}
    profile = {
        "role_id": ROLE,
        "years_experience": "5",
        "skill_ids": ["react"],
        "custom_skills": list(custom_skills),
        "break_started_on": "2024-01-01",
        "planned_return_date": "2024-06-01",
    }
    assert client.patch("/api/v1/profile", headers=headers, json=profile).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    chosen = client.put("/api/v1/practice-role", headers=headers, json={"role_id": ROLE, "source": "previous"})
    assert chosen.status_code == 200
    return headers


def _answer_current(headers, session):
    current_id = session["progress"]["current_scenario_id"]
    scenario = next(s for s in session["scenarios"] if s["scenario_id"] == current_id)
    path = f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{current_id}/response"
    response = client.post(path, headers=headers, json={"selected_option_id": scenario["options"][0]["option_id"]})
    assert response.status_code == 201
    return response.json()


def _play_through(headers):
    session = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()
    answered = []
    while session["progress"]["current_scenario_id"]:
        answered.append(_answer_current(headers, session)["scenario"])
        session = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()
    return session, answered


def test_activity_has_four_questions_and_shows_only_the_current_one():
    headers = _ready()

    session = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()

    assert session["progress"]["total_activities"] == 4
    assert session["progress"]["completed_activities"] == 0
    # Upcoming questions stay on the server.
    assert [s["status"] for s in session["scenarios"]] == ["current"]


def test_questions_unlock_one_at_a_time_with_authored_feedback():
    headers = _ready()

    session, answered = _play_through(headers)

    assert len(answered) == 4
    assert len({s["scenario_id"] for s in answered}) == 4
    assert all(s["feedback_status"] == "available" for s in answered)
    assert session["progress"]["completed_activities"] == 4
    assert session["progress"]["current_scenario_id"] is None


def test_nothing_new_is_left_after_every_question_is_answered():
    """AC 4.3.5."""
    headers = _ready()
    _play_through(headers)

    again = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)
    other_level = client.post(
        "/api/v1/practice-sessions", headers=headers, json={"duration": "standard", "difficulty": "standard"}
    )

    assert again.status_code == 409
    assert again.json()["error"]["code"] == "NO_NEW_ACTIVITIES"
    assert other_level.status_code == 201


def test_an_activity_must_be_finished_before_another_starts():
    headers = _ready()
    first = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()
    _answer_current(headers, first)

    again = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)
    other_level = client.post(
        "/api/v1/practice-sessions", headers=headers, json={"duration": "standard", "difficulty": "standard"}
    )

    for response in (again, other_level):
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "ACTIVITY_IN_PROGRESS"
    current = client.get("/api/v1/practice-sessions/current", headers=headers).json()
    assert current["session_id"] == first["session_id"]
    assert current["progress"]["completed_activities"] == 1


def test_a_finished_activity_is_kept_as_completed_when_the_next_starts():
    headers = _ready()
    finished, _ = _play_through(headers)

    client.post("/api/v1/practice-sessions", headers=headers, json={"duration": "standard", "difficulty": "standard"})

    kept = client.get(f"/api/v1/practice-sessions/{finished['session_id']}", headers=headers).json()
    assert kept["status"] == "completed"
    assert kept["completed_at"] is not None
    assert len([s for s in kept["scenarios"] if s["feedback_status"] == "available"]) == 4


def test_remaining_counts_new_questions_per_difficulty():
    headers = _ready()
    before = client.get("/api/v1/practice-sessions/remaining", headers=headers)
    _play_through(headers)

    after = client.get("/api/v1/practice-sessions/remaining", headers=headers)

    assert before.status_code == 200
    assert before.json()["multiple_choice"] == {"guided": 4, "standard": 4, "challenge": 4}
    assert after.json()["multiple_choice"] == {"guided": 0, "standard": 4, "challenge": 4}
    # Drag and drop is counted separately and is untouched by multiple choice.
    assert after.json()["drag_and_drop"] == before.json()["drag_and_drop"]


def test_custom_skill_adds_one_live_question_last(use_live_questions):
    """AC 4.4.6."""
    live = FakeLive()
    use_live_questions(live)
    headers = _ready(custom_skills=["Looker"])

    session, answered = _play_through(headers)

    assert session["progress"]["total_activities"] == 5
    assert answered[-1]["scenario_id"] == "web_developer_guided_live_v3_test"
    assert answered[-1]["feedback"]["skill_to_explore"]["skill"] == "Looker"
    # Only the role, the difficulty and skill names are sent.
    assert live.calls == [(ROLE, "guided", ["Looker"])]


def test_no_custom_skill_means_no_live_question(use_live_questions):
    live = FakeLive()
    use_live_questions(live)
    headers = _ready()

    session = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()

    assert session["progress"]["total_activities"] == 4
    assert live.calls == []


def test_a_broken_live_generator_never_fails_the_activity(use_live_questions):
    use_live_questions(BrokenLive())
    headers = _ready(custom_skills=["Looker"])

    response = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)

    assert response.status_code == 201
    assert response.json()["progress"]["total_activities"] == 4


def test_stored_option_feedback_is_never_sent_to_the_client(use_live_questions):
    use_live_questions(FakeLive())
    headers = _ready(custom_skills=["Looker"])

    session = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)

    assert "option_feedback" not in session.text


def test_practice_still_starts_when_earlier_activities_cannot_be_checked(monkeypatch):
    """AC 4.3.5 exception: some questions may repeat, and the response says so."""
    from fastapi import HTTPException

    from app.api import dependencies

    headers = _ready()
    normal = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()
    while normal["progress"]["current_scenario_id"]:
        _answer_current(headers, normal)
        normal = client.get(f"/api/v1/practice-sessions/{normal['session_id']}", headers=headers).json()

    def _down(owner):
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE", "message": "x"})

    monkeypatch.setattr(dependencies._practice_session_repository, "list_for_owner", _down)
    again = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)

    assert normal["history_checked"] is True
    assert again.status_code == 201
    assert again.json()["history_checked"] is False
    assert again.json()["progress"]["total_activities"] == 4


def test_live_question_is_added_after_the_activity_has_started(use_live_questions):
    """In production the live question is written off the request, so
    starting never waits for it."""
    from app.api import dependencies

    pending = []
    app.dependency_overrides[dependencies.get_background_runner] = lambda: pending.append
    use_live_questions(FakeLive())
    headers = _ready(custom_skills=["Looker"])

    started = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS).json()
    before = started["progress"]["total_activities"]
    first = _answer_current(headers, started)
    pending.pop()()  # the live question is ready
    session = client.get(f"/api/v1/practice-sessions/{started['session_id']}", headers=headers).json()

    assert before == 4
    assert session["progress"]["total_activities"] == 5
    # The answer saved in the meantime is untouched.
    assert session["progress"]["completed_activities"] == 1
    assert first["scenario"]["feedback_status"] == "available"
    answered = []
    while session["progress"]["current_scenario_id"]:
        answered.append(_answer_current(headers, session)["scenario"]["scenario_id"])
        session = client.get(f"/api/v1/practice-sessions/{started['session_id']}", headers=headers).json()
    assert answered[-1] == "web_developer_guided_live_v3_test"


def test_live_question_arriving_after_the_activity_finished_is_dropped(use_live_questions):
    from app.api import dependencies

    pending = []
    app.dependency_overrides[dependencies.get_background_runner] = lambda: pending.append
    use_live_questions(FakeLive())
    headers = _ready(custom_skills=["Looker"])

    session, answered = _play_through(headers)
    pending.pop()()
    after = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()

    assert len(answered) == 4
    assert after["progress"]["total_activities"] == 4


def test_questions_about_her_practice_focus_come_first(monkeypatch):
    """AC 4.4.5."""
    from app.api import dependencies
    from app.repositories.interfaces.catalogue_repository import CatalogueItem

    def _role_skills(role_id):
        return [
            CatalogueItem(id="react", label="React", in_demand=True),  # she already has it
            CatalogueItem(id="vue", label="Vue.js", in_demand=True),  # her next skill
            CatalogueItem(id="jenkins", label="Jenkins", in_demand=True),
        ]

    monkeypatch.setattr(dependencies._catalogue_repository, "get_skills_for_role", _role_skills)
    headers = _ready()

    session, answered = _play_through(headers)

    skills = [s["skills_used"] for s in answered]
    assert "Vue.js" in skills[0]
    assert "Jenkins" in skills[1]


def test_generated_ids_fit_the_database_column_for_the_longest_role_ids():
    from app.providers.live_question_provider import MAX_SCENARIO_ID_LENGTH, _fit_scenario_id

    long_id = "computer_and_information_research_scientist_challenge_live_v3_0123456789ab"
    short_id = "web_developer_guided_live_v3_0123456789ab"

    fitted = _fit_scenario_id(long_id)

    assert len(fitted) == MAX_SCENARIO_ID_LENGTH
    # The unique suffix and the "_live_" marker survive; the front is trimmed.
    assert fitted.endswith("_live_v3_0123456789ab")
    assert fitted.startswith("computer_and_information")
    assert _fit_scenario_id(short_id) == short_id
