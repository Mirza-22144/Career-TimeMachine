from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return the protected-route header."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _complete_and_confirm_profile(headers: dict[str, str]) -> None:
    """Create a confirmed profile so journey integration can be checked."""
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_id": "software_engineer",
            "years_experience": "5",
            "skill_ids": ["python"],
            "break_started_on": "2024-01-01",
            "planned_return_date": "2024-06-01",
        },
    )
    assert patch_response.status_code == 200

    confirm_response = client.post("/api/v1/profile/confirm", headers=headers)
    assert confirm_response.status_code == 200
    assert confirm_response.json()["confirmed"] is True


def test_get_career_direction_returns_empty_selection_for_new_profile():
    headers = _new_session_headers()

    response = client.get("/api/v1/career-direction", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "return_readiness": None,
        "area_to_explore": None,
    }


def test_patch_career_direction_saves_and_returns_both_fields():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={
            "return_readiness": "preparing",
            "area_to_explore": "cloud_native_engineering",
        },
    )
    get_response = client.get("/api/v1/career-direction", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "return_readiness": "preparing",
        "area_to_explore": "cloud_native_engineering",
    }
    assert get_response.status_code == 200
    assert get_response.json() == response.json()


def test_patch_career_direction_allows_partial_update_and_clear():
    headers = _new_session_headers()
    initial_response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={
            "return_readiness": "ready",
            "area_to_explore": "modern_devops",
        },
    )
    assert initial_response.status_code == 200

    response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={"area_to_explore": None},
    )

    assert response.status_code == 200
    assert response.json() == {
        "return_readiness": "ready",
        "area_to_explore": None,
    }


def test_patch_career_direction_rejects_invalid_return_readiness():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={"return_readiness": "almost_ready"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "HTTP_400",
            "message": "Invalid return_readiness: almost_ready",
            "details": [],
        }
    }


def test_patch_career_direction_rejects_invalid_area_to_explore():
    headers = _new_session_headers()

    response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={"area_to_explore": "quantum_architecture"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "HTTP_400",
            "message": "Invalid area_to_explore: quantum_architecture",
            "details": [],
        }
    }


def test_career_direction_feeds_current_return_status_in_journey():
    headers = _new_session_headers()
    _complete_and_confirm_profile(headers)

    direction_response = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={"return_readiness": "planning_soon"},
    )
    journey_response = client.get("/api/v1/career-journey", headers=headers)

    assert direction_response.status_code == 200
    assert journey_response.status_code == 200
    assert journey_response.json()["current_return_status"] == {
        "id": "planning_soon",
        "label": "I'm planning to return soon",
    }
