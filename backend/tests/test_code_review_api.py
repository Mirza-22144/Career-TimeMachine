"""Code Review activities (US 4.7) from the AI team's static pool, the
practice plan that says which activity is unlocked next, and the reason
attached to each suggested role."""

from fastapi.testclient import TestClient

from app.main import app
from app.providers.code_review_provider import AiCodeReviewProvider, scenario_id_for
from app.providers.ml_two_role_prediction_provider import MLTwoRolePredictionProvider
from app.providers.role_prediction_provider import RolePredictionRequest, SkillContext
from app.providers.two_role_prediction_provider import PredictedRolesContent

client = TestClient(app)

ROLE = "web_developer"  # in both the test catalogue and the code review pool
REVIEW = {"duration": "standard", "difficulty": "guided", "activity_type": "code_review"}


def _ready():
    token = client.post("/api/v1/anonymous-sessions").json()["token"]
    headers = {"X-Session-Token": token}
    profile = {
        "role_id": ROLE,
        "years_experience": "5",
        "skill_ids": ["react", "git", "sql"],
        "break_started_on": "2024-01-01",
        "planned_return_date": "2024-06-01",
    }
    assert client.patch("/api/v1/profile", headers=headers, json=profile).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    assert client.put("/api/v1/practice-role", headers=headers, json={"role_id": ROLE, "source": "previous"}).status_code == 200
    return headers


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in _all_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in _all_keys(child)}
    return set()


def _current(session):
    return next(s for s in session["scenarios"] if s["scenario_id"] == session["progress"]["current_scenario_id"])


def _answer(headers, session, option_index=0):
    scenario = _current(session)
    path = f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{scenario['scenario_id']}/response"
    return client.post(path, headers=headers, json={"selected_option_id": scenario["options"][option_index]["option_id"]})


def _finish(headers, settings):
    session = client.post("/api/v1/practice-sessions", headers=headers, json=settings).json()
    while session["progress"]["current_scenario_id"]:
        scenario = _current(session)
        body = (
            {"placements": dict(zip(("blank_1", "blank_2", "blank_3"), (o["option_id"] for o in scenario["options"])))}
            if scenario["activity_type"] == "drag_and_drop"
            else {"selected_option_id": scenario["options"][0]["option_id"]}
        )
        path = f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{scenario['scenario_id']}/response"
        assert client.post(path, headers=headers, json=body).status_code == 201
        session = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()
    return session


def test_a_code_review_activity_is_four_reviews_shown_one_at_a_time():
    headers = _ready()

    started = client.post("/api/v1/practice-sessions", headers=headers, json=REVIEW)

    assert started.status_code == 201
    session = started.json()
    assert session["progress"]["total_activities"] == 4
    assert [s["status"] for s in session["scenarios"]] == ["current"]
    scenario = _current(session)
    assert scenario["activity_type"] == "code_review"
    assert scenario["code_snippet"] and scenario["language"]
    assert len(scenario["options"]) == 4


def test_the_intended_option_and_other_options_feedback_are_never_sent():
    headers = _ready()

    started = client.post("/api/v1/practice-sessions", headers=headers, json=REVIEW)
    answered = _answer(headers, started.json())

    for response in (started, answered):
        assert not _all_keys(response.json()) & {"correct_option_id", "option_feedback", "content", "score", "is_correct"}


def test_answering_returns_the_feedback_written_for_that_option():
    """AC 4.7.2: what worked well and what else to consider, for the option
    she chose - whichever one it was."""
    headers = _ready()
    pool = AiCodeReviewProvider().static_activities(ROLE, "guided", set(), 4)
    session = client.post("/api/v1/practice-sessions", headers=headers, json=REVIEW).json()
    scenario = _current(session)
    authored = next(a for a in pool if a["scenario_id"] == scenario["scenario_id"])["content"]["option_feedback"]

    answered = _answer(headers, session, option_index=2).json()["scenario"]

    chosen = scenario["options"][2]["option_id"]
    assert answered["status"] == "completed"
    assert answered["feedback_status"] == "available"
    assert answered["feedback"]["what_worked_well"] == authored[chosen]["what_worked_well"]
    assert answered["feedback"]["areas_to_consider"] == authored[chosen]["areas_to_consider"]
    assert answered["feedback"]["skill_to_explore"]["skill"] == authored[chosen]["skill_to_explore"]["skill"]


def test_code_review_is_counted_and_exhausted_separately():
    headers = _ready()
    _finish(headers, REVIEW)

    again = client.post("/api/v1/practice-sessions", headers=headers, json=REVIEW)
    remaining = client.get("/api/v1/practice-sessions/remaining", headers=headers).json()

    assert again.status_code == 409
    assert again.json()["error"]["code"] == "NO_NEW_ACTIVITIES"
    assert remaining["code_review"] == {"guided": 0, "standard": 4, "challenge": 4}
    assert remaining["multiple_choice"]["guided"] == 4
    assert remaining["drag_and_drop"]["guided"] == 4


def test_every_pool_id_fits_the_database_column_and_stays_unique():
    provider = AiCodeReviewProvider()
    ids = [
        scenario_id_for(record["question_id"])
        for records in provider._by_role_difficulty.values()
        for record in records
    ]

    assert len(ids) == 324
    assert len(set(ids)) == 324
    assert max(len(i) for i in ids) <= 64


def test_the_plan_unlocks_one_activity_per_level_and_stays_put_until_she_finishes_one():
    headers = _ready()

    first = client.get("/api/v1/practice-sessions/plan", headers=headers).json()
    same = client.get("/api/v1/practice-sessions/plan", headers=headers).json()

    kinds = {"multiple_choice", "drag_and_drop", "code_review"}
    assert first["last_difficulty"] is None
    assert set(first["next_activity"]) == {"guided", "standard", "challenge"}
    assert all(kind in kinds for kind in first["next_activity"].values())
    assert same == first

    unlocked = first["next_activity"]["guided"]
    _finish(headers, {"duration": "standard", "difficulty": "guided", "activity_type": unlocked})
    after = client.get("/api/v1/practice-sessions/plan", headers=headers).json()

    assert after["last_difficulty"] == "guided"
    assert after["remaining"][unlocked]["guided"] == 0
    # What she just finished is not offered again; another kind is unlocked.
    assert after["next_activity"]["guided"] in kinds - {unlocked}


def test_the_plan_offers_nothing_at_a_level_once_all_three_are_done():
    headers = _ready()
    for kind in ("multiple_choice", "drag_and_drop", "code_review"):
        _finish(headers, {"duration": "standard", "difficulty": "guided", "activity_type": kind})

    plan = client.get("/api/v1/practice-sessions/plan", headers=headers).json()

    assert plan["next_activity"]["guided"] is None
    assert plan["next_activity"]["standard"] is not None


def test_each_suggested_role_comes_with_a_reason_and_no_score():
    """AI team's explainability handover: the same two roles as before, each
    with a plain-language summary built from her role and skills."""
    request = RolePredictionRequest(
        role_id="software_developer",
        role_label="Software Developer",
        skills=(SkillContext(id="python", label="Python"), SkillContext(id="sql", label="SQL")),
    )

    content = PredictedRolesContent.model_validate(MLTwoRolePredictionProvider().predict(request))

    assert len(content.predicted_roles) == 2
    for role in content.predicted_roles:
        assert role.explanation is not None
        assert len(role.explanation.summary) >= 30
        assert "model_profile_match" in role.explanation.reason_codes
        assert "%" not in role.explanation.summary
        assert not {"score", "probability", "confidence"} & set(role.explanation.model_dump())
