"""Drag and Drop activities (US 4.6): a message with three gaps and five
phrases. Which phrase is meant for which gap stays on the server, nothing
is graded, and the activity runs through the same sessions as multiple
choice."""

from fastapi.testclient import TestClient

from app.api import dependencies
from app.main import app
from app.providers.drag_and_drop_provider import AiDragDropProvider, to_scenario

client = TestClient(app)

ROLE = "web_developer"  # in both the test catalogue and the drag and drop pool
DND = {"duration": "standard", "difficulty": "guided", "activity_type": "drag_and_drop"}
MCQ = {"duration": "standard", "difficulty": "guided"}

LIVE_ACTIVITY = {
    "title": "Explaining a Looker delay",
    "situation": "A Looker dashboard you own is late and a manager needs an update.",
    "sentence_template": "The dashboard is late because {blank_1}. It will be ready by {blank_2}. Meanwhile, {blank_3}.",
    "blanks": [{"blank_id": "blank_1"}, {"blank_id": "blank_2"}, {"blank_id": "blank_3"}],
    "options": [
        {"option_id": "o1", "text": "a source table changed", "fits_blank_id": "blank_1"},
        {"option_id": "o2", "text": "noon tomorrow", "fits_blank_id": "blank_2"},
        {"option_id": "o3", "text": "I will share yesterday's figures", "fits_blank_id": "blank_3"},
        {"option_id": "o4", "text": "something broke", "fits_blank_id": None},
        {"option_id": "o5", "text": "soon", "fits_blank_id": None},
    ],
    "feedback_by_option": {
        "o1": {"what_to_improve": None, "why": "Names the cause."},
        "o2": {"what_to_improve": None, "why": "Gives a time."},
        "o3": {"what_to_improve": None, "why": "Offers a next step."},
        "o4": {"what_to_improve": "Name the cause.", "why": "Reads as vague."},
        "o5": {"what_to_improve": "Give a time.", "why": "Cannot be planned around."},
    },
    "skills_used": ["Looker"],
    "guidance": ["Say what happened, when it will be fixed, and what happens next."],
}


class WithLive(AiDragDropProvider):
    def __init__(self):
        super().__init__(api_key="")
        self.calls = []

    def live_activity(self, role_id, difficulty, custom_skills, years_experience, responsibilities):
        self.calls.append((role_id, difficulty, list(custom_skills), years_experience, list(responsibilities)))
        return to_scenario(f"{role_id}_{difficulty}_dd_live_test", "Web Developer", LIVE_ACTIVITY)


def _ready(custom_skills=()):
    token = client.post("/api/v1/anonymous-sessions").json()["token"]
    headers = {"X-Session-Token": token}
    profile = {
        "role_id": ROLE,
        "years_experience": "5",
        "skill_ids": ["react"],
        "custom_skills": list(custom_skills),
        "custom_responsibilities": ["Mentoring juniors"],
        "break_started_on": "2024-01-01",
        "planned_return_date": "2024-06-01",
    }
    assert client.patch("/api/v1/profile", headers=headers, json=profile).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    assert client.put("/api/v1/practice-role", headers=headers, json={"role_id": ROLE, "source": "previous"}).status_code == 200
    return headers


def _current(session):
    return next(s for s in session["scenarios"] if s["scenario_id"] == session["progress"]["current_scenario_id"])


def _submit(headers, session, placements):
    scenario = _current(session)
    path = f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{scenario['scenario_id']}/response"
    return client.post(path, headers=headers, json={"placements": placements})


def _first_three(scenario):
    ids = [option["option_id"] for option in scenario["options"]]
    return {"blank_1": ids[0], "blank_2": ids[1], "blank_3": ids[2]}


def test_a_drag_and_drop_activity_is_four_messages_shown_one_at_a_time():
    headers = _ready()

    started = client.post("/api/v1/practice-sessions", headers=headers, json=DND)

    assert started.status_code == 201
    session = started.json()
    assert session["progress"]["total_activities"] == 4
    assert [s["status"] for s in session["scenarios"]] == ["current"]
    scenario = _current(session)
    assert scenario["activity_type"] == "drag_and_drop"
    assert len(scenario["options"]) == 5
    for blank in ("{blank_1}", "{blank_2}", "{blank_3}"):
        assert scenario["sentence_template"].count(blank) == 1
    assert scenario["phrase_feedback"] is None and scenario["completed_message"] is None


def test_which_phrase_fits_which_gap_is_never_sent():
    headers = _ready()

    started = client.post("/api/v1/practice-sessions", headers=headers, json=DND)

    for hidden in ("fits_blank_id", '"fits"', "feedback_by_option", "what_to_improve", '"content"'):
        assert hidden not in started.text
    assert set(_current(started.json())["options"][0]) == {"option_id", "text"}


def test_submitting_shows_the_message_and_how_each_phrase_comes_across():
    """AC 4.6.2: no score, no count, and "what would work better" only for a
    phrase that does not fit where she put it."""
    headers = _ready()
    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    scenario = _current(session)
    placements = _first_three(scenario)

    response = _submit(headers, session, placements)

    assert response.status_code == 201
    answered = response.json()["scenario"]
    assert answered["status"] == "completed"
    assert answered["feedback_status"] == "available"
    assert answered["response"]["placements"] == placements
    assert "{blank_" not in answered["completed_message"]
    feedback = answered["phrase_feedback"]
    assert [f["blank_id"] for f in feedback] == ["blank_1", "blank_2", "blank_3"]
    assert [f["option_id"] for f in feedback] == list(placements.values())
    assert all(f["comes_across"] for f in feedback)
    for banned in ("score", "correct", "incorrect", "wrong", "is_fit", '"fits'):
        assert banned not in response.text.lower()
    # The next message is unlocked.
    assert response.json()["progress"]["completed_activities"] == 1
    assert response.json()["progress"]["current_scenario_id"] != scenario["scenario_id"]


def test_a_fitting_phrase_in_the_wrong_gap_gets_a_gentle_note(monkeypatch):
    provider = WithLive()
    app.dependency_overrides[dependencies.get_drag_drop_provider] = lambda: provider
    headers = _ready()
    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    stored = dependencies._practice_session_repository.get_for_owner(
        next(iter(dependencies._practice_session_repository._sessions.values())).owner_token_hash,
        session["session_id"],
    )
    fits = next(s for s in stored.scenarios if s.status == "current").content["fits"]
    by_blank = {blank: option for option, blank in fits.items() if blank}
    distractor = next(option for option, blank in fits.items() if blank is None)
    # Two phrases swapped, and one that fits no gap.
    placements = {"blank_1": by_blank["blank_2"], "blank_2": by_blank["blank_1"], "blank_3": distractor}

    feedback = _submit(headers, session, placements).json()["scenario"]["phrase_feedback"]

    assert all(f["what_would_work_better"] for f in feedback)
    assert "different gap" in feedback[0]["what_would_work_better"]


def test_placements_must_fill_every_gap_with_this_activitys_phrases():
    headers = _ready()
    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    good = _first_three(_current(session))

    two_gaps = _submit(headers, session, {"blank_1": good["blank_1"], "blank_2": good["blank_2"]})
    same_phrase = _submit(headers, session, {**good, "blank_3": good["blank_1"]})
    foreign = _submit(headers, session, {**good, "blank_3": "o9"})
    wrong_kind = client.post(
        f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{_current(session)['scenario_id']}/response",
        headers=headers,
        json={"selected_option_id": good["blank_1"]},
    )

    for response in (two_gaps, same_phrase, foreign):
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_PLACEMENTS"
    assert wrong_kind.status_code == 400
    assert wrong_kind.json()["error"]["code"] == "ACTIVITY_TYPE_MISMATCH"


def test_drag_and_drop_and_multiple_choice_are_separate_activities():
    headers = _ready()
    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    while session["progress"]["current_scenario_id"]:
        assert _submit(headers, session, _first_three(_current(session))).status_code == 201
        session = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()

    again = client.post("/api/v1/practice-sessions", headers=headers, json=DND)
    multiple_choice = client.post("/api/v1/practice-sessions", headers=headers, json=MCQ)
    remaining = client.get("/api/v1/practice-sessions/remaining", headers=headers).json()

    assert again.status_code == 409
    assert again.json()["error"]["code"] == "NO_NEW_ACTIVITIES"
    assert multiple_choice.status_code == 201
    assert remaining["drag_and_drop"]["guided"] == 0
    assert remaining["drag_and_drop"]["standard"] == 4


def test_a_typed_in_skill_adds_one_live_message_last():
    provider = WithLive()
    app.dependency_overrides[dependencies.get_drag_drop_provider] = lambda: provider
    headers = _ready(custom_skills=["Looker"])

    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    answered = []
    while session["progress"]["current_scenario_id"]:
        answered.append(_submit(headers, session, _first_three(_current(session))).json()["scenario"]["scenario_id"])
        session = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()

    assert len(answered) == 5
    assert answered[-1] == "web_developer_guided_dd_live_test"
    # What the live generator is given: role, level, her own skills, years
    # of experience and responsibilities - as agreed with the AI team.
    assert provider.calls == [(ROLE, "guided", ["Looker"], "5", ["Mentoring juniors"])]


def test_no_typed_in_skill_means_no_live_message():
    provider = WithLive()
    app.dependency_overrides[dependencies.get_drag_drop_provider] = lambda: provider
    headers = _ready()

    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()

    assert session["progress"]["total_activities"] == 4
    assert provider.calls == []


def test_completed_drag_and_drop_shows_on_the_dashboard_list():
    headers = _ready()
    session = client.post("/api/v1/practice-sessions", headers=headers, json=DND).json()
    title = _current(session)["title"]
    _submit(headers, session, _first_three(_current(session)))

    recent = client.get("/api/v1/practice-sessions/recent-activities", headers=headers).json()

    assert recent[0]["title"] == title
    assert recent[0]["activity_type"] == "drag_and_drop"


def test_phrases_are_shuffled_so_order_does_not_give_the_gaps_away():
    provider = AiDragDropProvider(api_key="")

    orders = {
        tuple(option["option_id"] for option in provider.static_activities(ROLE, "guided", set(), 1)[0]["options"])
        for _ in range(30)
    }

    assert len(orders) > 1
