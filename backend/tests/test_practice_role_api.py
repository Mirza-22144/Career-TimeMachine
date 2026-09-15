"""Selected practice role and practice context (backend Subtask 5, AC 4.1.2)."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.interfaces.profile_repository import Profile
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.services.practice_role_service import PracticeContext, PracticeRoleService

client = TestClient(app)

PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python", "git"],
    "custom_skills": ["Private side project"],
    "responsibility_ids": ["api_design"],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}

EMPTY_SELECTION = {"role_id": None, "role_label": None, "source": None}
PREVIOUS_SELECTION = {
    "role_id": "software_engineer",
    "role_label": "Software Engineer",
    "source": "previous",
}


def _new_headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _save_confirmed_profile(headers: dict[str, str], **overrides) -> None:
    body = {**PROFILE, **overrides}
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200


def _select(headers: dict[str, str], role_id: str, source: str):
    return client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": role_id, "source": source},
    )


def test_new_token_has_no_practice_role():
    response = client.get("/api/v1/practice-role", headers=_new_headers())

    assert response.status_code == 200
    assert response.json() == EMPTY_SELECTION


def test_previous_role_is_saved_and_survives_refresh():
    headers = _new_headers()
    _save_confirmed_profile(headers)

    response = _select(headers, "software_engineer", "previous")

    assert response.status_code == 200
    assert response.json() == PREVIOUS_SELECTION
    # A refresh is a later request from a client with no other state.
    assert TestClient(app).get("/api/v1/practice-role", headers=headers).json() == PREVIOUS_SELECTION


def test_predicted_role_is_saved_with_its_source():
    headers = _new_headers()
    _save_confirmed_profile(headers)

    response = _select(headers, "web_developer", "predicted")

    expected = {"role_id": "web_developer", "role_label": "Web Developer", "source": "predicted"}
    assert response.status_code == 200
    assert response.json() == expected
    assert client.get("/api/v1/practice-role", headers=headers).json() == expected


@pytest.mark.parametrize(
    ("role_id", "source", "message"),
    [
        ("astronaut", "predicted", "Invalid role_id: astronaut"),
        ("web_developer", "previous", "role_id must match the saved previous role"),
        ("other", "predicted", "Invalid role_id: other"),
    ],
)
def test_invalid_role_is_rejected_and_existing_choice_kept(role_id, source, message):
    headers = _new_headers()
    _save_confirmed_profile(headers)
    assert _select(headers, "software_engineer", "previous").status_code == 200

    response = _select(headers, role_id, source)

    assert response.status_code == 400
    assert response.json() == {"error": {"code": "HTTP_400", "message": message, "details": []}}
    assert client.get("/api/v1/practice-role", headers=headers).json() == PREVIOUS_SELECTION


def test_previous_role_requires_a_saved_previous_role():
    response = _select(_new_headers(), "software_engineer", "previous")

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "role_id must match the saved previous role"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"role_id": "software_engineer"},
        {"source": "previous"},
        {"role_id": "software_engineer", "source": "future"},
        {"role_id": "", "source": "predicted"},
        {"role_id": "a" * 65, "source": "predicted"},
        {"role_id": "Software Engineer", "source": "predicted"},
        {"role_id": "software_engineer", "source": "previous", "unexpected": True},
    ],
)
def test_malformed_selection_fails_request_validation(body):
    response = client.put("/api/v1/practice-role", headers=_new_headers(), json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_previous_selection_clears_when_previous_role_is_edited():
    headers = _new_headers()
    _save_confirmed_profile(headers)
    _select(headers, "software_engineer", "previous")

    client.patch("/api/v1/profile", headers=headers, json={"role_id": "qa_engineer"})

    assert client.get("/api/v1/practice-role", headers=headers).json() == EMPTY_SELECTION


def test_predicted_selection_survives_profile_edits():
    headers = _new_headers()
    _save_confirmed_profile(headers)
    _select(headers, "web_developer", "predicted")

    client.patch("/api/v1/profile", headers=headers, json={"years_experience": "7"})
    client.post("/api/v1/profile/confirm", headers=headers)

    assert client.get("/api/v1/practice-role", headers=headers).json()["role_id"] == "web_developer"


def test_other_previous_role_uses_the_entered_role_title():
    headers = _new_headers()
    _save_confirmed_profile(headers, role_id="other", role_other_text="Mainframe Specialist")

    response = _select(headers, "other", "previous")

    assert response.status_code == 200
    assert response.json()["role_label"] == "Mainframe Specialist"


def test_one_token_cannot_read_or_change_another_tokens_practice_role():
    headers_a = _new_headers()
    headers_b = _new_headers()
    _save_confirmed_profile(headers_a)
    _save_confirmed_profile(headers_b)
    _select(headers_a, "software_engineer", "previous")

    b_before = client.get("/api/v1/practice-role", headers=headers_b).json()
    b_change = _select(headers_b, "web_developer", "predicted")

    assert b_before == EMPTY_SELECTION
    assert b_change.status_code == 200
    assert client.get("/api/v1/practice-role", headers=headers_a).json() == PREVIOUS_SELECTION


@pytest.mark.parametrize("method", ["GET", "PUT"])
def test_practice_role_requires_a_valid_token(method):
    body = {"role_id": "software_engineer", "source": "previous"} if method == "PUT" else None

    response = client.request(
        method,
        "/api/v1/practice-role",
        headers={"X-Session-Token": "not-a-real-token"},
        json=body,
    )

    assert response.status_code == 401


def test_practice_context_uses_saved_career_information_only(fake_catalogue):
    profiles = MemoryProfileRepository()
    profiles.save(
        Profile(
            session_token="owner",
            role_id="software_engineer",
            years_experience="5",
            skill_ids=["python", "git", "retired_skill"],
            custom_skills=["Private side project"],
            responsibility_ids=["api_design"],
            custom_responsibilities=["Family business"],
            break_reason="caregiving",
            confirmed=True,
            practice_role_id="web_developer",
            practice_role_source="predicted",
        )
    )

    context = PracticeRoleService(profiles, fake_catalogue).build_practice_context("owner")

    # Custom free text, break details and the owner key are not included.
    assert context == PracticeContext(
        role_id="web_developer",
        role_label="Web Developer",
        role_source="predicted",
        years_experience="5 years",
        skills=["Python", "Git"],
        responsibilities=["API design"],
    )


@pytest.mark.parametrize(
    ("stored", "code"),
    [
        (None, "PROFILE_NOT_CONFIRMED"),
        (
            Profile(session_token="owner", role_id="web_developer", practice_role_id="web_developer",
                    practice_role_source="previous"),
            "PROFILE_NOT_CONFIRMED",
        ),
        (Profile(session_token="owner", role_id="web_developer", confirmed=True), "PRACTICE_ROLE_REQUIRED"),
    ],
)
def test_practice_context_explains_missing_information(fake_catalogue, stored, code):
    profiles = MemoryProfileRepository()
    if stored is not None:
        profiles.save(stored)

    with pytest.raises(HTTPException) as error:
        PracticeRoleService(profiles, fake_catalogue).build_practice_context("owner")

    assert error.value.status_code == 409
    assert error.value.detail["code"] == code
