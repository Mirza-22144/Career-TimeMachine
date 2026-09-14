"""Regression tests for CTM-F-001: a rejected profile update must not change
the stored profile (repeat of pen-test CTM-PT-005b)."""

from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.interfaces.profile_repository import Profile
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.schemas.profile import ProfileUpdate
from app.services.profile_service import ProfileService

client = TestClient(app)

VALID_PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python"],
    "custom_skills": ["Mentoring"],
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return its auth header for tests."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _save_confirmed_profile(headers: dict[str, str]) -> dict:
    """Save and confirm a valid profile, returning the confirmed body."""
    assert client.patch("/api/v1/profile", headers=headers, json=VALID_PROFILE).status_code == 200
    confirmed = client.post("/api/v1/profile/confirm", headers=headers)
    assert confirmed.status_code == 200
    return confirmed.json()


def test_rejected_date_update_leaves_stored_profile_unchanged():
    headers = _new_session_headers()
    before = _save_confirmed_profile(headers)

    # Moving the break start after the planned return date breaks the date rule.
    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"break_started_on": "2024-09-01"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == (
        "planned_return_date must be on or after break_started_on"
    )
    after = client.get("/api/v1/profile", headers=headers).json()
    assert after == before
    assert after["break_started_on"] == "2024-01-01"
    assert after["confirmed"] is True


def test_rejected_update_does_not_partially_apply_valid_fields():
    headers = _new_session_headers()
    before = _save_confirmed_profile(headers)

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"custom_skills": ["Changed"], "planned_return_date": "2023-12-01"},
    )

    assert response.status_code == 400
    assert client.get("/api/v1/profile", headers=headers).json() == before


def test_rejected_catalogue_id_does_not_partially_apply_valid_fields():
    headers = _new_session_headers()
    before = _save_confirmed_profile(headers)

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"custom_skills": ["Changed"], "years_experience": "four-ish"},
    )

    assert response.status_code == 400
    assert client.get("/api/v1/profile", headers=headers).json() == before


def test_valid_edit_after_confirmation_still_updates_profile():
    headers = _new_session_headers()
    _save_confirmed_profile(headers)

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"planned_return_date": "2024-09-01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["planned_return_date"] == "2024-09-01"
    assert body["break_duration_months"] == 8
    assert body["confirmed"] is False
    assert client.get("/api/v1/profile", headers=headers).json() == body


def test_service_rejected_update_keeps_previous_stored_values():
    profiles = MemoryProfileRepository()
    service = ProfileService(profiles, MemoryCatalogueRepository())
    service.update_profile(
        "owner",
        ProfileUpdate(break_started_on=date(2024, 1, 1), planned_return_date=date(2024, 6, 1)),
    )

    with pytest.raises(HTTPException) as error:
        service.update_profile("owner", ProfileUpdate(planned_return_date=date(2023, 1, 1)))

    assert error.value.status_code == 400
    stored = profiles.get_by_session_token("owner")
    assert stored.planned_return_date == date(2024, 6, 1)
    assert stored.break_duration_months == 5


def test_memory_profile_repository_only_changes_on_save():
    profiles = MemoryProfileRepository()
    profiles.save(Profile(session_token="owner", custom_skills=["A"]))

    loaded = profiles.get_by_session_token("owner")
    loaded.role_id = "web_developer"
    loaded.custom_skills.append("B")

    assert profiles.get_by_session_token("owner") == Profile(
        session_token="owner",
        custom_skills=["A"],
    )
