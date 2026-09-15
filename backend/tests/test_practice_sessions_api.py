"""Workplace-practice session setup (backend Subtask 6; AC 4.1.3, 4.2.2, 4.3.4)."""

import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.tokens import hash_token
from app.main import app
from app.providers.curated_scenario_provider import CuratedScenarioProvider
from app.providers.scenario_provider import ScenarioProviderError
from app.repositories.interfaces.profile_repository import Profile
from app.repositories.memory.memory_practice_session_repository import (
    MemoryPracticeSessionRepository,
)
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.schemas.practice_session import PracticeSessionCreate
from app.services.practice_role_service import PracticeRoleService
from app.services.practice_session_service import PracticeSessionService

client = TestClient(app)

PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python", "git"],
    "custom_skills": ["Secret hobby project"],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}
SETTINGS = {"duration": "standard", "difficulty": "guided"}
UNKNOWN_ID = "0" * 32


class FailingProvider(CuratedScenarioProvider):
    def generate_scenario(self, request):
        raise ScenarioProviderError("provider is down")


class InvalidScenarioProvider(CuratedScenarioProvider):
    def generate_scenario(self, request):
        return {"title": "Missing most fields", "score": 10}


class CrashingProvider(CuratedScenarioProvider):
    def generate_scenario(self, request):
        raise RuntimeError("unexpected internal detail")


class MismatchedActivityProvider(CuratedScenarioProvider):
    """Returns a valid written scenario when multiple choice was requested."""

    def generate_scenario(self, request):
        scenario = super().generate_scenario(request)
        return {**scenario, "activity_type": "written_response", "options": []}


class RecordingProvider(CuratedScenarioProvider):
    def __init__(self) -> None:
        self.requests = []

    def generate_scenario(self, request):
        self.requests.append(request)
        return super().generate_scenario(request)


def _new_token() -> str:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return response.json()["token"]


def _headers(token: str | None = None) -> dict[str, str]:
    return {"X-Session-Token": token or _new_token()}


def _ready_for_practice(headers, role_id="software_engineer", source="previous") -> None:
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    selection = client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": role_id, "source": source},
    )
    assert selection.status_code == 200


def _start(headers, settings=SETTINGS):
    return client.post("/api/v1/practice-sessions", headers=headers, json=settings)


def test_start_practice_uses_saved_role_career_context_and_settings():
    headers = _headers()
    _ready_for_practice(headers)

    response = _start(headers)

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == {"id": "software_engineer", "label": "Software Engineer", "source": "previous"}
    assert (body["duration"], body["duration_minutes"], body["difficulty"]) == ("standard", 10, "guided")
    assert body["status"] == "active"
    assert body["completed_at"] is None
    assert body["created_at"] == body["updated_at"]
    assert "owner_token_hash" not in body

    [scenario] = body["scenarios"]
    assert scenario["status"] == "current"
    assert scenario["situation"] and scenario["task"]
    assert scenario["activity_type"] == "multiple_choice"
    assert len(scenario["options"]) >= 2
    assert len(scenario["guidance"]) == 3
    assert {"Python", "Git"} <= set(scenario["skills_used"])
    assert scenario["response"] is None
    assert scenario["feedback"] is None
    assert scenario["feedback_status"] is None
    assert body["progress"] == {
        "status": "active",
        "total_activities": 1,
        "completed_activities": 0,
        "current_scenario_id": scenario["scenario_id"],
    }


def test_written_response_sessions_remain_available(use_activity_type):
    use_activity_type("written_response")
    headers = _headers()
    _ready_for_practice(headers)

    [scenario] = _start(headers).json()["scenarios"]

    assert scenario["activity_type"] == "written_response"
    assert scenario["options"] == []
    assert scenario["task"].startswith("Write")


def test_predicted_role_gets_a_scenario_for_that_role():
    headers = _headers()
    _ready_for_practice(headers, role_id="data_analyst", source="predicted")

    body = _start(headers).json()

    assert body["role"] == {"id": "data_analyst", "label": "Data Analyst", "source": "predicted"}
    assert body["scenarios"][0]["scenario_id"].startswith("data_")


@pytest.mark.parametrize(("duration", "minutes"), [("quick", 5), ("standard", 10), ("challenge", 15)])
@pytest.mark.parametrize("difficulty", ["guided", "standard", "challenge"])
def test_every_supported_duration_and_difficulty_is_accepted(duration, minutes, difficulty):
    headers = _headers()
    _ready_for_practice(headers)

    response = _start(headers, {"duration": duration, "difficulty": difficulty})

    assert response.status_code == 201
    assert response.json()["duration_minutes"] == minutes
    assert response.json()["difficulty"] == difficulty


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"duration": "standard"},
        {"difficulty": "guided"},
        {"duration": "long", "difficulty": "guided"},
        {"duration": "standard", "difficulty": "expert"},
        {"duration": 10, "difficulty": "guided"},
        {**SETTINGS, "role_id": "web_developer"},
    ],
)
def test_invalid_settings_are_rejected_without_starting_practice(body):
    headers = _headers()
    _ready_for_practice(headers)

    response = _start(headers, body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert client.get("/api/v1/practice-sessions/current", headers=headers).status_code == 404


def test_active_session_can_be_retrieved_after_refresh():
    headers = _headers()
    _ready_for_practice(headers)
    started = _start(headers).json()

    refreshed_client = TestClient(app)
    current = refreshed_client.get("/api/v1/practice-sessions/current", headers=headers)
    by_id = refreshed_client.get(f"/api/v1/practice-sessions/{started['session_id']}", headers=headers)

    assert current.status_code == 200
    assert current.json() == started
    assert by_id.json() == started


def test_missing_profile_or_role_gives_a_clear_error():
    headers = _headers()

    no_profile = _start(headers)
    client.patch("/api/v1/profile", headers=headers, json=PROFILE)
    client.post("/api/v1/profile/confirm", headers=headers)
    no_role = _start(headers)

    assert no_profile.status_code == 409
    assert no_profile.json()["error"]["code"] == "PROFILE_NOT_CONFIRMED"
    assert no_role.status_code == 409
    assert no_role.json()["error"]["code"] == "PRACTICE_ROLE_REQUIRED"
    current = client.get("/api/v1/practice-sessions/current", headers=headers)
    assert current.status_code == 404
    assert current.json()["error"]["code"] == "PRACTICE_SESSION_NOT_FOUND"


def test_starting_again_replaces_the_active_session():
    headers = _headers()
    _ready_for_practice(headers)
    first = _start(headers).json()

    second = _start(headers).json()

    old = client.get(f"/api/v1/practice-sessions/{first['session_id']}", headers=headers).json()
    assert second["session_id"] != first["session_id"]
    assert old["status"] == "abandoned"
    assert old["progress"]["current_scenario_id"] is None
    current = client.get("/api/v1/practice-sessions/current", headers=headers).json()
    assert current["session_id"] == second["session_id"]


def test_completing_a_session_is_recorded_and_repeatable():
    headers = _headers()
    _ready_for_practice(headers)
    started = _start(headers).json()
    path = f"/api/v1/practice-sessions/{started['session_id']}/complete"

    completed = client.post(path, headers=headers)
    again = client.post(path, headers=headers)

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] is not None
    assert completed.json()["progress"]["status"] == "completed"
    assert again.json() == completed.json()
    assert client.get("/api/v1/practice-sessions/current", headers=headers).status_code == 404


def test_abandoned_session_cannot_be_completed():
    headers = _headers()
    _ready_for_practice(headers)
    first = _start(headers).json()
    _start(headers)

    response = client.post(f"/api/v1/practice-sessions/{first['session_id']}/complete", headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PRACTICE_SESSION_NOT_ACTIVE"


def test_one_token_cannot_see_or_change_another_tokens_session():
    headers_a = _headers()
    headers_b = _headers()
    _ready_for_practice(headers_a)
    _ready_for_practice(headers_b)
    session_id = _start(headers_a).json()["session_id"]

    missing = client.get(f"/api/v1/practice-sessions/{UNKNOWN_ID}", headers=headers_b)
    b_read = client.get(f"/api/v1/practice-sessions/{session_id}", headers=headers_b)
    b_complete = client.post(f"/api/v1/practice-sessions/{session_id}/complete", headers=headers_b)
    b_current = client.get("/api/v1/practice-sessions/current", headers=headers_b)

    # Another user's session looks exactly like one that does not exist.
    assert b_read.status_code == 404
    assert b_read.json() == missing.json()
    assert b_complete.status_code == 404
    assert b_current.status_code == 404
    a_view = client.get(f"/api/v1/practice-sessions/{session_id}", headers=headers_a).json()
    assert a_view["status"] == "active"


def test_overlong_session_id_fails_validation():
    response = client.get(f"/api/v1/practice-sessions/{'x' * 65}", headers=_headers())

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/v1/practice-sessions"),
        ("GET", "/api/v1/practice-sessions/current"),
        ("GET", f"/api/v1/practice-sessions/{UNKNOWN_ID}"),
        ("POST", f"/api/v1/practice-sessions/{UNKNOWN_ID}/complete"),
    ],
)
def test_practice_sessions_require_a_valid_token(method, path):
    response = client.request(
        method,
        path,
        headers={"X-Session-Token": "not-a-real-token"},
        json=SETTINGS if method == "POST" else None,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "provider",
    [FailingProvider(), InvalidScenarioProvider(), CrashingProvider(), MismatchedActivityProvider()],
)
def test_provider_failure_returns_controlled_error_and_stores_nothing(use_provider, provider):
    headers = _headers()
    _ready_for_practice(headers)
    use_provider(provider)

    response = _start(headers)

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SCENARIO_UNAVAILABLE",
            "message": "A practice scenario could not be prepared. Please try again.",
            "details": [],
        }
    }
    assert "provider is down" not in response.text
    assert "unexpected internal detail" not in response.text
    assert client.get("/api/v1/practice-sessions/current", headers=headers).status_code == 404


def test_provider_receives_only_the_career_context_it_needs(use_provider):
    recording = RecordingProvider()
    use_provider(recording)
    token = _new_token()
    headers = _headers(token)
    _ready_for_practice(headers)

    assert _start(headers).status_code == 201

    [request] = recording.requests
    assert request.role_id == "software_engineer"
    assert request.years_experience == "5 years"
    assert request.skills == ("Python", "Git")
    assert (request.duration, request.difficulty) == ("standard", "guided")
    assert request.activity_type == "multiple_choice"
    sent = repr(request)
    for private in (token, hash_token(token), "Secret hobby project", "caregiving", "2024-01-01"):
        assert private not in sent


def _service_ready_for_practice(fake_catalogue, provider, timeout=10.0):
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
    sessions = MemoryPracticeSessionRepository()
    service = PracticeSessionService(
        sessions,
        PracticeRoleService(profiles, fake_catalogue),
        provider,
        provider_timeout_seconds=timeout,
    )
    return service, sessions


def test_slow_provider_times_out_with_a_controlled_error(fake_catalogue):
    class SlowProvider(CuratedScenarioProvider):
        def generate_scenario(self, request):
            time.sleep(0.5)
            return super().generate_scenario(request)

    service, sessions = _service_ready_for_practice(fake_catalogue, SlowProvider(), timeout=0.05)

    with pytest.raises(HTTPException) as error:
        service.start_session("owner", PracticeSessionCreate(**SETTINGS))

    assert error.value.status_code == 503
    assert error.value.detail["code"] == "SCENARIO_UNAVAILABLE"
    assert sessions.get_active_for_owner("owner") is None


def test_session_store_is_scoped_by_owner_and_only_changes_on_save(fake_catalogue):
    service, sessions = _service_ready_for_practice(fake_catalogue, CuratedScenarioProvider())
    started = service.start_session("owner", PracticeSessionCreate(**SETTINGS))

    loaded = sessions.get_for_owner("owner", started.session_id)
    loaded.status = "completed"
    loaded.scenarios.clear()

    assert sessions.get_for_owner("someone-else", started.session_id) is None
    assert sessions.get_for_owner("owner", started.session_id) == started
