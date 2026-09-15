"""Token validation, returning-user access and isolation between tokens
(US 3.1-3.3, backend Subtask 4)."""

import logging
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from app.core.tokens import hash_token
from app.main import app
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.repositories.memory.memory_session_repository import MemorySessionRepository
from app.schemas.profile import ProfileUpdate
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService

client = TestClient(app)

SAVED_PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python"],
    "break_reason": "prefer_not_to_say",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}

PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/anonymous-sessions/current"),
    ("GET", "/api/v1/profile"),
    ("PATCH", "/api/v1/profile"),
    ("POST", "/api/v1/profile/confirm"),
    ("DELETE", "/api/v1/profile"),
    ("GET", "/api/v1/career-journey"),
    ("GET", "/api/v1/career-translation"),
    ("GET", "/api/v1/career-direction"),
    ("PATCH", "/api/v1/career-direction"),
]

INVALID_TOKEN_ERROR = {
    "error": {"code": "HTTP_401", "message": "Invalid session token", "details": []}
}


def _new_token() -> str:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return response.json()["token"]


def _headers(token: str) -> dict[str, str]:
    return {"X-Session-Token": token}


def _save_confirmed_profile(token: str) -> None:
    assert client.patch("/api/v1/profile", headers=_headers(token), json=SAVED_PROFILE).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=_headers(token)).status_code == 200


def test_generated_tokens_are_unique_and_url_safe():
    tokens = {_new_token() for _ in range(5)}

    assert len(tokens) == 5
    for token in tokens:
        assert len(token) == 43
        assert all(char.isalnum() or char in "-_" for char in token)


def test_valid_token_is_recognised_without_echoing_it():
    token = _new_token()

    response = client.get("/api/v1/anonymous-sessions/current", headers=_headers(token))

    assert response.status_code == 200
    assert set(response.json()) == {"created_at", "last_seen_at"}
    assert token not in response.text


@pytest.mark.parametrize(
    "bad_token",
    ["unknown-but-well-formed-token", "CTM-ABCD-EFGH", "", "has spaces", "x" * 129, "<script>"],
)
def test_unknown_and_malformed_tokens_get_the_same_401(bad_token):
    response = client.get("/api/v1/anonymous-sessions/current", headers=_headers(bad_token))

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_ERROR


@pytest.mark.parametrize(("method", "path"), PROTECTED_ENDPOINTS)
def test_protected_endpoints_reject_missing_and_invalid_tokens(method, path):
    body = {} if method == "PATCH" else None

    missing = client.request(method, path, json=body)
    invalid = client.request(method, path, headers=_headers("not-a-real-token"), json=body)

    assert missing.status_code == 401
    assert missing.json()["error"]["message"] == "Missing session token"
    assert invalid.status_code == 401
    assert invalid.json() == INVALID_TOKEN_ERROR


def test_returning_with_the_same_token_restores_saved_profile_and_journey():
    token = _new_token()
    _save_confirmed_profile(token)

    # A returning visit is a later request from a client with no other state.
    returning_client = TestClient(app)
    profile = returning_client.get("/api/v1/profile", headers=_headers(token))
    journey = returning_client.get("/api/v1/career-journey", headers=_headers(token))

    assert profile.status_code == 200
    assert profile.json()["role_id"] == "software_engineer"
    assert profile.json()["skill_ids"] == ["python"]
    assert profile.json()["confirmed"] is True
    assert journey.status_code == 200
    assert journey.json()["previous_role"] == {"id": "software_engineer", "label": "Software Engineer"}


def test_editing_with_the_same_token_updates_the_existing_profile():
    token = _new_token()
    _save_confirmed_profile(token)

    edit = client.patch("/api/v1/profile", headers=_headers(token), json={"years_experience": "7"})
    reconfirm = client.post("/api/v1/profile/confirm", headers=_headers(token))
    profile = client.get("/api/v1/profile", headers=_headers(token)).json()

    assert edit.status_code == 200
    assert reconfirm.status_code == 200
    assert profile["years_experience"] == "7"
    assert profile["role_id"] == "software_engineer"
    assert profile["skill_ids"] == ["python"]
    assert profile["confirmed"] is True


def test_one_token_cannot_read_or_change_another_tokens_data():
    token_a = _new_token()
    token_b = _new_token()
    _save_confirmed_profile(token_a)
    a_before = client.get("/api/v1/profile", headers=_headers(token_a)).json()

    b_profile = client.get("/api/v1/profile", headers=_headers(token_b))
    b_journey = client.get("/api/v1/career-journey", headers=_headers(token_b))
    b_patch = client.patch("/api/v1/profile", headers=_headers(token_b), json={"role_id": "web_developer"})
    b_direction = client.patch(
        "/api/v1/career-direction", headers=_headers(token_b), json={"return_readiness": "ready"}
    )
    b_delete = client.delete("/api/v1/profile", headers=_headers(token_b))

    assert b_profile.json()["role_id"] is None
    assert b_profile.json()["confirmed"] is False
    assert b_journey.status_code == 409
    assert b_patch.status_code == 200
    assert b_direction.status_code == 200
    assert b_delete.status_code == 204
    assert client.get("/api/v1/profile", headers=_headers(token_a)).json() == a_before
    assert client.get("/api/v1/career-direction", headers=_headers(token_a)).json() == {
        "return_readiness": None,
        "area_to_explore": None,
    }


def test_session_store_keeps_only_the_token_hash():
    sessions = MemorySessionRepository()
    service = SessionService(sessions)

    issued = service.start_session()
    stored = sessions.get_by_token_hash(hash_token(issued.token))

    assert stored is not None
    assert issued.token not in asdict(stored).values()
    assert service.get_current(issued.token) == stored


def test_malformed_token_is_rejected_before_storage_lookup():
    class RecordingSessionRepository(MemorySessionRepository):
        def __init__(self) -> None:
            super().__init__()
            self.lookups: list[str] = []

        def get_by_token_hash(self, token_hash):
            self.lookups.append(token_hash)
            return super().get_by_token_hash(token_hash)

    sessions = RecordingSessionRepository()
    service = SessionService(sessions)

    assert service.get_current("x" * 129) is None
    assert service.get_current("bad token!") is None
    assert sessions.lookups == []


def test_validating_a_token_records_the_visit():
    sessions = MemorySessionRepository()
    service = SessionService(sessions)
    issued = service.start_session()

    session = service.get_current(issued.token)

    assert session is not None
    assert session.last_seen_at >= issued.last_seen_at
    assert sessions.get_by_token_hash(hash_token(issued.token)).last_seen_at == session.last_seen_at


def test_profile_store_keeps_one_profile_per_token_across_edits():
    profiles = MemoryProfileRepository()
    service = ProfileService(profiles, MemoryCatalogueRepository())
    owner = hash_token("some-access-token")

    service.update_profile(owner, ProfileUpdate(years_experience="3"))
    service.update_profile(owner, ProfileUpdate(years_experience="5"))

    assert list(profiles._profiles) == [owner]
    assert profiles.get_by_session_token(owner).years_experience == "5"


def test_token_is_not_written_to_logs(caplog):
    caplog.set_level(logging.DEBUG)

    token = _new_token()
    client.get("/api/v1/anonymous-sessions/current", headers=_headers(token))
    client.patch("/api/v1/profile", headers=_headers(token), json={"years_experience": "3"})

    assert token not in caplog.text
