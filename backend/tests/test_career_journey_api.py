from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return the header used by protected APIs."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _complete_and_confirm_profile(headers: dict[str, str]) -> None:
    """Create a confirmed profile for journey tests."""
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "software_engineer",
            "years_experience": "10_plus",
            "skill_ids": ["python", "rest_apis"],
            "custom_skills": ["Team leadership", "Legacy system support"],
            "break_reason": "prefer_not_to_say",
            "break_started_on": "2023-01-01",
            "planned_return_date": "2024-01-01",
        },
    )
    assert patch_response.status_code == 200

    confirm_response = client.post("/api/v1/profile/confirm", headers=headers)
    assert confirm_response.status_code == 200
    assert confirm_response.json()["confirmed"] is True


def test_career_journey_requires_confirmed_profile():
    headers = _new_session_headers()

    response = client.get("/api/v1/career-journey", headers=headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "profile not confirmed"


def test_career_journey_returns_structured_confirmed_profile_summary():
    headers = _new_session_headers()
    _complete_and_confirm_profile(headers)

    response = client.get("/api/v1/career-journey", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "previous_role": {
            "id": "software_engineer",
            "label": "Software Engineer",
        },
        "years_experience": {
            "id": "10_plus",
            "label": "10+ years",
        },
        "career_break": {
            "break_started_on": "2023-01-01",
            "planned_return_date": "2024-01-01",
            "return_date_unsure": False,
            "break_duration_months": 12,
        },
        "current_return_status": None,
        "selected_skills": {
            "catalogue_skills": [
                {"id": "python", "label": "Python"},
                {"id": "rest_apis", "label": "REST APIs"},
            ],
            "custom_skills": ["Team leadership", "Legacy system support"],
        },
        "strengths": [],
    }


def test_career_journey_keeps_planned_return_null_when_return_date_unsure():
    headers = _new_session_headers()
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "qa_engineer",
            "years_experience": "5",
            "skill_ids": ["git"],
            "break_started_on": "2024-01-01",
            "planned_return_date": "2024-12-01",
            "return_date_unsure": True,
        },
    )
    assert patch_response.status_code == 200

    confirm_response = client.post("/api/v1/profile/confirm", headers=headers)
    assert confirm_response.status_code == 200

    response = client.get("/api/v1/career-journey", headers=headers)

    assert response.status_code == 200
    career_break = response.json()["career_break"]
    assert career_break["planned_return_date"] is None
    assert career_break["return_date_unsure"] is True
