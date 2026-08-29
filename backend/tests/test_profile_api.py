from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return its auth header for tests."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def test_get_profile_creates_empty_draft_for_session():
    headers = _new_session_headers()

    response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["role_id"] is None
    assert body["skill_ids"] == []
    assert body["custom_skills"] == []
    assert body["confirmed"] is False


def test_patch_profile_cleans_custom_lists_and_calculates_duration():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "software_engineer",
            "years_experience": "5",
            "skill_ids": ["python", "rest_apis"],
            "custom_skills": [" Mentoring ", "", "mentoring", "Legacy systems"],
            "break_started_on": "2024-01-15",
            "planned_return_date": "2024-04-15",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["custom_skills"] == ["Mentoring", "Legacy systems"]
    assert body["break_duration_months"] == 3


def test_patch_rejects_invalid_catalogue_id():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"years_experience": "four-ish"},
    )

    assert response.status_code == 400
    assert "Invalid years_experience" in response.json()["detail"]


def test_patch_rejects_return_date_before_break_start():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "break_started_on": "2024-06-01",
            "planned_return_date": "2024-05-31",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "planned_return_date must be on or after break_started_on"
    )


def test_confirm_incomplete_profile_lists_missing_fields():
    headers = _new_session_headers()

    response = client.post("/api/v1/profile/confirm", headers=headers)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["message"] == "Profile is incomplete"
    assert "role_id" in detail["missing"]
    assert "years_experience" in detail["missing"]
    assert "break_started_on" in detail["missing"]
    assert "planned_return_date" in detail["missing"]


def test_confirm_requires_other_text_for_other_role_and_break_reason():
    headers = _new_session_headers()

    client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "other",
            "years_experience": "7",
            "break_reason": "other",
            "break_started_on": "2024-01-01",
            "return_date_unsure": True,
        },
    )

    response = client.post("/api/v1/profile/confirm", headers=headers)

    assert response.status_code == 400
    missing = response.json()["detail"]["missing"]
    assert "role_other_text" in missing
    assert "break_reason_other_text" in missing
    assert "planned_return_date" not in missing


def test_confirm_complete_profile_sets_confirmed_true():
    headers = _new_session_headers()
    client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "software_engineer",
            "years_experience": "10_plus",
            "break_reason": "prefer_not_to_say",
            "break_started_on": "2023-01-01",
            "planned_return_date": "2024-01-01",
        },
    )

    response = client.post("/api/v1/profile/confirm", headers=headers)

    assert response.status_code == 200
    assert response.json()["confirmed"] is True


def test_patch_after_confirmation_resets_confirmed_false():
    headers = _new_session_headers()
    client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "software_engineer",
            "years_experience": "3",
            "break_started_on": "2024-01-01",
            "planned_return_date": "2024-02-01",
        },
    )
    confirmed = client.post("/api/v1/profile/confirm", headers=headers)
    assert confirmed.json()["confirmed"] is True

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"custom_skills": ["Project leadership"]},
    )

    assert response.status_code == 200
    assert response.json()["confirmed"] is False


def test_delete_profile_removes_current_session_profile():
    headers = _new_session_headers()
    client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"role_id": "software_engineer"},
    )

    delete_response = client.delete("/api/v1/profile", headers=headers)
    get_response = client.get("/api/v1/profile", headers=headers)

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 200
    assert get_response.json()["role_id"] is None
