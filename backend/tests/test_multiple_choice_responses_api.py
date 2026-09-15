"""Multiple-choice workplace activities, active in Iteration 2 (backend
Subtask 8; AC 4.4.2, 4.5.1, 4.5.2, 4.5.3): selecting one option, reflective
feedback, progress and access rules."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.tokens import hash_token
from app.main import app
from app.providers.curated_scenario_provider import CURATED_SCENARIOS, CuratedScenarioProvider
from app.providers.scenario_provider import ScenarioProviderError
from app.repositories.interfaces.profile_repository import Profile
from app.repositories.memory.memory_practice_session_repository import (
    MemoryPracticeSessionRepository,
)
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.schemas.practice_session import PracticeSessionCreate
from app.schemas.scenario_response import ScenarioResponseCreate
from app.services.practice_role_service import PracticeRoleService
from app.services.practice_session_service import PracticeSessionService
from app.services.scenario_response_service import ScenarioResponseService

client = TestClient(app)

PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python"],
    "custom_skills": ["Secret hobby project"],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}
SETTINGS = {"duration": "quick", "difficulty": "standard"}
UNKNOWN_ID = "0" * 32
OTHER_SCENARIO_OPTION_ID = CURATED_SCENARIOS["data"][0].options[0].option_id
JUDGEMENT_KEYS = {
    "score", "grade", "result", "passed", "pass_fail", "rating", "employability",
    "is_correct", "correct_option_id", "readiness",
}
JUDGEMENT_WORDS = ("correct", "score", "pass/fail", "employab", "readiness")


class FailingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        raise ScenarioProviderError("feedback model is down")


class LabellingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        feedback = super().generate_feedback(request)
        feedback["what_worked_well"] = ["That was the correct option."]
        return feedback


class MarkingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        return {**super().generate_feedback(request), "is_correct": True}


class RecordingFeedbackProvider(CuratedScenarioProvider):
    def __init__(self) -> None:
        self.feedback_requests = []

    def generate_feedback(self, request):
        self.feedback_requests.append(request)
        return super().generate_feedback(request)


def _new_token() -> str:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return response.json()["token"]


def _started_practice(token: str | None = None):
    """Return (headers, session body) for a user with an active session."""
    headers = {"X-Session-Token": token or _new_token()}
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    assert client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": "software_engineer", "source": "previous"},
    ).status_code == 200
    started = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)
    assert started.status_code == 201
    return headers, started.json()


def _option_ids(session: dict) -> list[str]:
    return [option["option_id"] for option in session["scenarios"][0]["options"]]


def _response_path(session: dict, scenario_id: str | None = None) -> str:
    scenario_id = scenario_id or session["scenarios"][0]["scenario_id"]
    return f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{scenario_id}/response"


def _choose(headers, session, option_id=None, scenario_id=None):
    option_id = option_id or _option_ids(session)[1]
    return client.post(
        _response_path(session, scenario_id),
        headers=headers,
        json={"selected_option_id": option_id},
    )


def _stored_scenario(headers, session) -> dict:
    stored = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers)
    return stored.json()["scenarios"][0]


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in _all_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in _all_keys(child)}
    return set()


# --- API -------------------------------------------------------------------


def test_practice_starts_with_a_single_selection_multiple_choice_activity():
    _, session = _started_practice()

    [scenario] = session["scenarios"]

    assert scenario["activity_type"] == "multiple_choice"
    assert scenario["situation"]
    assert scenario["task"].endswith("?")
    assert len(scenario["options"]) >= 2
    assert len(set(_option_ids(session))) == len(scenario["options"])
    assert all(set(option) == {"option_id", "text"} and option["text"] for option in scenario["options"])
    assert scenario["response"] is None
    assert session["progress"]["current_scenario_id"] == scenario["scenario_id"]


def test_full_token_to_multiple_choice_feedback_journey():
    headers, session = _started_practice()
    option_id = _option_ids(session)[1]

    response = _choose(headers, session, option_id)

    assert response.status_code == 201
    body = response.json()
    scenario = body["scenario"]
    assert body["session_id"] == session["session_id"]
    assert scenario["status"] == "completed"
    assert scenario["response"]["selected_option_id"] == option_id
    assert scenario["response"]["response_text"] is None
    assert scenario["response"]["submitted_at"]
    assert scenario["feedback_status"] == "available"
    feedback = scenario["feedback"]
    assert feedback["what_worked_well"]
    assert feedback["trade_offs"]
    assert feedback["areas_to_consider"]
    assert feedback["skill_to_explore"]["skill"] == scenario["new_skill_focus"]
    assert body["progress"] == {
        "status": "active",
        "total_activities": 1,
        "completed_activities": 1,
        "current_scenario_id": None,
    }
    assert not _all_keys(body) & JUDGEMENT_KEYS
    feedback_text = str(feedback).lower()
    assert not any(word in feedback_text for word in JUDGEMENT_WORDS)


def test_feedback_reflects_on_whichever_option_was_selected():
    headers_a, session_a = _started_practice()
    headers_b, session_b = _started_practice()

    feedback_a = _choose(headers_a, session_a, _option_ids(session_a)[0]).json()["scenario"]["feedback"]
    feedback_b = _choose(headers_b, session_b, _option_ids(session_b)[2]).json()["scenario"]["feedback"]

    assert feedback_a["what_worked_well"] != feedback_b["what_worked_well"]
    assert feedback_a["trade_offs"] != feedback_b["trade_offs"]


def test_selected_option_feedback_and_progress_can_be_resumed_later():
    headers, session = _started_practice()
    submitted = _choose(headers, session).json()

    returning_client = TestClient(app)
    current = returning_client.get("/api/v1/practice-sessions/current", headers=headers)
    progress = returning_client.get(
        f"/api/v1/practice-sessions/{session['session_id']}/progress", headers=headers
    )

    assert current.json()["scenarios"][0] == submitted["scenario"]
    assert progress.json() == submitted["progress"]


@pytest.mark.parametrize("second_choice", [0, 1])
def test_duplicate_submission_is_rejected_and_first_choice_kept(second_choice):
    headers, session = _started_practice()
    first = _choose(headers, session, _option_ids(session)[1]).json()

    duplicate = _choose(headers, session, _option_ids(session)[second_choice])

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESPONSE_ALREADY_SUBMITTED"
    assert _stored_scenario(headers, session) == first["scenario"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"selected_option_id": None},
        {"selected_option_id": ""},
        {"selected_option_id": "Option A"},
        {"selected_option_id": "x" * 65},
        {"selected_option_id": 1},
        {"selected_option_id": ["software_slow_release_a", "software_slow_release_b"]},
        {"selected_option_id": "software_slow_release_a", "response_text": "I would review it."},
        {"selected_option_id": "software_slow_release_a", "is_correct": True},
    ],
)
def test_missing_or_malformed_option_is_rejected_and_nothing_saved(body):
    headers, session = _started_practice()

    response = client.post(_response_path(session), headers=headers, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert _stored_scenario(headers, session)["response"] is None


def test_multiple_choice_rejects_a_written_response():
    headers, session = _started_practice()

    response = client.post(_response_path(session), headers=headers, json={"response_text": "I would review it."})

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "ACTIVITY_TYPE_MISMATCH",
            "message": "This activity expects selected_option_id",
            "details": [],
        }
    }
    assert _stored_scenario(headers, session)["response"] is None


@pytest.mark.parametrize("option_id", ["option_z", OTHER_SCENARIO_OPTION_ID])
def test_unknown_option_or_option_from_another_scenario_is_rejected(option_id):
    headers, session = _started_practice()

    response = _choose(headers, session, option_id)

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_OPTION_ID",
            "message": "selected_option_id is not an option for this scenario",
            "details": [],
        }
    }
    stored = _stored_scenario(headers, session)
    assert stored["response"] is None
    assert stored["status"] == "current"
    assert _choose(headers, session).status_code == 201


def test_option_for_a_scenario_outside_the_session_is_not_found():
    headers, session = _started_practice()

    response = _choose(headers, session, _option_ids(session)[0], scenario_id="data_dashboard_mismatch")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCENARIO_NOT_FOUND"


def test_one_token_cannot_submit_an_option_for_another_tokens_session():
    headers_a, session_a = _started_practice()
    headers_b, _ = _started_practice()

    unknown = _choose(headers_b, {**session_a, "session_id": UNKNOWN_ID}, _option_ids(session_a)[0])
    b_submit = _choose(headers_b, session_a, _option_ids(session_a)[0])

    assert b_submit.status_code == 404
    assert b_submit.json() == unknown.json()
    assert _stored_scenario(headers_a, session_a)["response"] is None
    assert _choose(headers_a, session_a).status_code == 201


def test_options_are_only_accepted_for_an_active_session():
    headers, first = _started_practice()
    client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)  # abandons first
    headers_completed, completed = _started_practice()
    client.post(f"/api/v1/practice-sessions/{completed['session_id']}/complete", headers=headers_completed)

    for response in (_choose(headers, first), _choose(headers_completed, completed)):
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PRACTICE_SESSION_NOT_ACTIVE"


def test_multiple_choice_submission_requires_a_valid_token():
    response = client.post(
        f"/api/v1/practice-sessions/{UNKNOWN_ID}/scenarios/any/response",
        headers={"X-Session-Token": "not-a-real-token"},
        json={"selected_option_id": "software_slow_release_a"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "provider",
    [FailingFeedbackProvider(), LabellingFeedbackProvider(), MarkingFeedbackProvider()],
)
def test_feedback_failure_or_correctness_label_still_saves_the_choice(use_provider, provider):
    headers, session = _started_practice()
    use_provider(provider)
    option_id = _option_ids(session)[0]

    response = _choose(headers, session, option_id)

    assert response.status_code == 201
    scenario = response.json()["scenario"]
    assert scenario["response"]["selected_option_id"] == option_id
    assert scenario["feedback"] is None
    assert scenario["feedback_status"] == "unavailable"
    assert response.json()["progress"]["completed_activities"] == 1
    for leaked in ("feedback model is down", "correct option", "is_correct"):
        assert leaked not in response.text


def test_feedback_request_contains_the_choice_but_no_identifiers(use_provider):
    recording = RecordingFeedbackProvider()
    use_provider(recording)
    token = _new_token()
    headers, session = _started_practice(token)
    options = session["scenarios"][0]["options"]

    assert _choose(headers, session, options[1]["option_id"]).status_code == 201

    [request] = recording.feedback_requests
    assert request.activity_type == "multiple_choice"
    assert request.selected_option_id == options[1]["option_id"]
    assert request.selected_option_text == options[1]["text"]
    assert request.option_texts == tuple(option["text"] for option in options)
    assert request.response_text is None
    sent = repr(request)
    for private in (token, hash_token(token), session["session_id"], "Secret hobby project", "caregiving"):
        assert private not in sent


# --- Service ---------------------------------------------------------------


def _services(fake_catalogue, activity_type="multiple_choice"):
    profiles = MemoryProfileRepository()
    profiles.save(
        Profile(
            session_token="owner",
            role_id="software_engineer",
            years_experience="5",
            confirmed=True,
            practice_role_id="software_engineer",
            practice_role_source="previous",
        )
    )
    repository = MemoryPracticeSessionRepository()
    sessions = PracticeSessionService(
        repository,
        PracticeRoleService(profiles, fake_catalogue),
        CuratedScenarioProvider(),
        activity_type=activity_type,
    )
    return sessions, ScenarioResponseService(sessions), repository


def test_service_saves_the_selected_option_through_the_repository(fake_catalogue):
    sessions, responses, repository = _services(fake_catalogue)
    started = sessions.start_session("owner", PracticeSessionCreate(**SETTINGS))
    scenario = started.scenarios[0]
    option_id = scenario.options[0].option_id

    result = responses.submit_response(
        "owner", started.session_id, scenario.scenario_id, ScenarioResponseCreate(selected_option_id=option_id)
    )

    stored = repository.get_for_owner("owner", started.session_id).scenarios[0]
    assert stored.response.selected_option_id == option_id
    assert stored.response.response_text is None
    assert stored.feedback.trade_offs
    assert stored.status == "completed"
    assert result.progress.completed_activities == 1
    assert result.progress.current_scenario_id is None


def test_service_rejects_an_unknown_option_without_saving(fake_catalogue):
    sessions, responses, repository = _services(fake_catalogue)
    started = sessions.start_session("owner", PracticeSessionCreate(**SETTINGS))
    scenario_id = started.scenarios[0].scenario_id

    with pytest.raises(HTTPException) as error:
        responses.submit_response(
            "owner", started.session_id, scenario_id, ScenarioResponseCreate(selected_option_id=OTHER_SCENARIO_OPTION_ID)
        )

    assert error.value.status_code == 400
    assert error.value.detail["code"] == "INVALID_OPTION_ID"
    stored = repository.get_for_owner("owner", started.session_id)
    assert stored.scenarios[0].response is None
    assert stored.progress.completed_activities == 0


def test_service_still_supports_written_responses(fake_catalogue):
    sessions, responses, repository = _services(fake_catalogue, activity_type="written_response")
    started = sessions.start_session("owner", PracticeSessionCreate(**SETTINGS))
    scenario = started.scenarios[0]

    result = responses.submit_response(
        "owner",
        started.session_id,
        scenario.scenario_id,
        ScenarioResponseCreate(response_text="I would begin by reviewing the tests and logs."),
    )

    assert scenario.activity_type == "written_response"
    assert scenario.options == []
    assert result.scenario.response.response_text == "I would begin by reviewing the tests and logs."
    assert result.scenario.response.selected_option_id is None
    assert result.scenario.feedback_status == "available"
