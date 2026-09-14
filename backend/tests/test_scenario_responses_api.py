"""Written scenario responses, reflective feedback and practice progress
(backend Subtask 8; AC 4.4.2, 4.5.1, 4.5.2, 4.5.3).

Written responses are retained for later iterations. Multiple choice, the
active Iteration 2 activity, is covered in test_multiple_choice_responses_api.py."""

import builtins
import logging

import pytest
from fastapi.testclient import TestClient

from app.core.tokens import hash_token
from app.main import app
from app.providers.curated_scenario_provider import CuratedScenarioProvider
from app.providers.scenario_provider import ScenarioProviderError

client = TestClient(app)


@pytest.fixture(autouse=True)
def written_activities(use_activity_type):
    use_activity_type("written_response")


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
ANSWER = (
    "I would first check what changed in this morning's release and look at the monitoring "
    "dashboards to see where the time is being spent. I would use my Debugging experience to "
    "compare slow and fast requests, and I would send support a short update every thirty minutes."
)
UNKNOWN_ID = "0" * 32
JUDGEMENT_KEYS = {
    "score", "grade", "result", "passed", "pass_fail", "rating", "employability",
    "is_correct", "correct_option_id", "readiness",
}


class FailingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        raise ScenarioProviderError("feedback model is down")


class CrashingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        raise RuntimeError("unexpected internal detail")


class ScoringFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        return {**super().generate_feedback(request), "score": 8}


class JudgingFeedbackProvider(CuratedScenarioProvider):
    def generate_feedback(self, request):
        feedback = super().generate_feedback(request)
        feedback["what_worked_well"] = ["You passed this activity with 8/10."]
        return feedback


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


def _response_path(session: dict, scenario_id: str | None = None) -> str:
    scenario_id = scenario_id or session["scenarios"][0]["scenario_id"]
    return f"/api/v1/practice-sessions/{session['session_id']}/scenarios/{scenario_id}/response"


def _submit(headers, session, text=ANSWER, scenario_id=None):
    return client.post(_response_path(session, scenario_id), headers=headers, json={"response_text": text})


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in _all_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in _all_keys(child)}
    return set()


def test_full_token_to_feedback_journey():
    headers, session = _started_practice()

    response = _submit(headers, session)

    assert response.status_code == 201
    body = response.json()
    scenario = body["scenario"]
    assert body["session_id"] == session["session_id"]
    assert scenario["status"] == "completed"
    assert scenario["response"]["response_text"] == ANSWER
    assert scenario["response"]["submitted_at"]
    assert scenario["feedback_status"] == "available"
    assert scenario["feedback"]["what_worked_well"]
    assert scenario["feedback"]["areas_to_consider"]
    assert scenario["feedback"]["skill_to_explore"]["skill"] == scenario["new_skill_focus"]
    assert scenario["feedback"]["skill_to_explore"]["why_relevant"]
    assert body["progress"] == {
        "status": "active",
        "total_activities": 1,
        "completed_activities": 1,
        "current_scenario_id": None,
    }
    assert not _all_keys(body) & JUDGEMENT_KEYS


def test_saved_response_feedback_and_progress_can_be_resumed_later():
    headers, session = _started_practice()
    submitted = _submit(headers, session).json()

    returning_client = TestClient(app)
    current = returning_client.get("/api/v1/practice-sessions/current", headers=headers)
    progress = returning_client.get(
        f"/api/v1/practice-sessions/{session['session_id']}/progress", headers=headers
    )

    assert current.status_code == 200
    assert current.json()["scenarios"][0] == submitted["scenario"]
    assert current.json()["progress"] == submitted["progress"]
    assert progress.status_code == 200
    assert progress.json() == submitted["progress"]


def test_progress_before_any_response_shows_the_current_scenario():
    headers, session = _started_practice()

    progress = client.get(f"/api/v1/practice-sessions/{session['session_id']}/progress", headers=headers)

    assert progress.json() == session["progress"]
    assert progress.json()["current_scenario_id"] == session["scenarios"][0]["scenario_id"]


def test_duplicate_submission_is_rejected_and_first_response_kept():
    headers, session = _started_practice()
    first = _submit(headers, session).json()

    duplicate = _submit(headers, session, text="A different answer")

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESPONSE_ALREADY_SUBMITTED"
    stored = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()
    assert stored["scenarios"][0] == first["scenario"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"response_text": ""},
        {"response_text": "   \n  "},
        {"response_text": "x" * 5001},
        {"response_text": 42},
        {"response_text": "An answer", "score": 5},
        {"response_text": "An answer", "selected_option_id": "option_a"},
    ],
)
def test_invalid_response_is_rejected_and_nothing_saved(body):
    headers, session = _started_practice()

    response = client.post(_response_path(session), headers=headers, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    stored = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()
    assert stored["scenarios"][0]["response"] is None


def test_longest_allowed_response_is_accepted():
    headers, session = _started_practice()

    assert _submit(headers, session, text="x" * 5000).status_code == 201


def test_written_scenario_rejects_a_selected_option_and_saves_nothing():
    headers, session = _started_practice()

    response = client.post(_response_path(session), headers=headers, json={"selected_option_id": "option_a"})

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "ACTIVITY_TYPE_MISMATCH",
            "message": "This activity expects response_text",
            "details": [],
        }
    }
    stored = client.get(f"/api/v1/practice-sessions/{session['session_id']}", headers=headers).json()
    assert stored["scenarios"][0]["response"] is None


def test_unknown_scenario_or_session_is_not_found():
    headers, session = _started_practice()

    unknown_scenario = _submit(headers, session, scenario_id="not_in_this_session")
    unknown_session = _submit(headers, {**session, "session_id": UNKNOWN_ID})

    assert unknown_scenario.status_code == 404
    assert unknown_scenario.json()["error"]["code"] == "SCENARIO_NOT_FOUND"
    assert unknown_session.status_code == 404
    assert unknown_session.json()["error"]["code"] == "PRACTICE_SESSION_NOT_FOUND"


def test_responses_are_only_accepted_for_an_active_session():
    headers, first = _started_practice()
    client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)  # abandons first
    headers_completed, completed = _started_practice()
    client.post(f"/api/v1/practice-sessions/{completed['session_id']}/complete", headers=headers_completed)

    abandoned_response = _submit(headers, first)
    completed_response = _submit(headers_completed, completed)

    for response in (abandoned_response, completed_response):
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PRACTICE_SESSION_NOT_ACTIVE"


def test_one_token_cannot_answer_or_read_another_tokens_practice():
    headers_a, session_a = _started_practice()
    headers_b, _ = _started_practice()

    unknown = _submit(headers_b, {**session_a, "session_id": UNKNOWN_ID})
    b_submit = _submit(headers_b, session_a)
    b_progress = client.get(f"/api/v1/practice-sessions/{session_a['session_id']}/progress", headers=headers_b)

    assert b_submit.status_code == 404
    assert b_submit.json() == unknown.json()
    assert b_progress.status_code == 404
    a_view = client.get(f"/api/v1/practice-sessions/{session_a['session_id']}", headers=headers_a).json()
    assert a_view["scenarios"][0]["response"] is None


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", f"/api/v1/practice-sessions/{UNKNOWN_ID}/scenarios/any/response"),
        ("GET", f"/api/v1/practice-sessions/{UNKNOWN_ID}/progress"),
    ],
)
def test_responses_and_progress_require_a_valid_token(method, path):
    response = client.request(
        method,
        path,
        headers={"X-Session-Token": "not-a-real-token"},
        json={"response_text": ANSWER} if method == "POST" else None,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "provider",
    [FailingFeedbackProvider(), CrashingFeedbackProvider(), ScoringFeedbackProvider(), JudgingFeedbackProvider()],
)
def test_feedback_failure_still_saves_the_response(use_provider, provider):
    headers, session = _started_practice()
    use_provider(provider)

    response = _submit(headers, session)

    assert response.status_code == 201
    scenario = response.json()["scenario"]
    assert scenario["status"] == "completed"
    assert scenario["response"]["response_text"] == ANSWER
    assert scenario["feedback"] is None
    assert scenario["feedback_status"] == "unavailable"
    assert response.json()["progress"]["completed_activities"] == 1
    for leaked in ("feedback model is down", "unexpected internal detail", "8/10"):
        assert leaked not in response.text


def test_submitted_code_is_stored_as_text_and_never_executed():
    headers, session = _started_practice()
    code = "import builtins\nbuiltins.ctm_code_was_executed = True\nprint('hello')"

    response = _submit(headers, session, text=code)

    assert response.status_code == 201
    assert response.json()["scenario"]["response"]["response_text"] == code
    assert not hasattr(builtins, "ctm_code_was_executed")


def test_feedback_request_contains_the_response_but_no_identifiers(use_provider):
    recording = RecordingFeedbackProvider()
    use_provider(recording)
    token = _new_token()
    headers, session = _started_practice(token)

    assert _submit(headers, session).status_code == 201

    [request] = recording.feedback_requests
    assert request.response_text == ANSWER
    assert request.role_label == "Software Engineer"
    sent = repr(request)
    for private in (token, hash_token(token), session["session_id"], "Secret hobby project", "caregiving"):
        assert private not in sent


def test_response_text_and_token_are_not_logged(caplog):
    caplog.set_level(logging.DEBUG)
    token = _new_token()
    headers, session = _started_practice(token)

    _submit(headers, session)

    assert ANSWER not in caplog.text
    assert token not in caplog.text
