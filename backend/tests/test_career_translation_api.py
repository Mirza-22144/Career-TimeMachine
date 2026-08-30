from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return the protected-route header."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


# AC 2.2.1: compares recorded skills against current in-demand skills for
# the user's previous role ("New Horizons"), not a skill-to-area mapping.


def test_career_translation_marks_in_demand_owned_skills_as_still_relevant():
    headers = _new_session_headers()
    client.patch("/api/v1/profile", headers=headers, json={"role_id": "web_developer"})
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"skill_ids": ["react", "aws"], "custom_skills": ["Release coordination"]},
    )
    assert patch_response.status_code == 200

    response = client.get("/api/v1/career-translation", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["role_data_available"] is True
    owned_by_id = {s["id"]: s for s in body["owned_skills"]}
    assert owned_by_id["react"]["still_relevant"] is True  # in-demand for web_developer
    assert owned_by_id["aws"]["still_relevant"] is False  # not in-demand for web_developer
    assert body["custom_skills"] == ["Release coordination"]


def test_career_translation_lists_unrecorded_in_demand_skills_as_new_horizons():
    headers = _new_session_headers()
    client.patch("/api/v1/profile", headers=headers, json={"role_id": "web_developer"})
    client.patch("/api/v1/profile", headers=headers, json={"skill_ids": ["react"]})

    response = client.get("/api/v1/career-translation", headers=headers)

    assert response.status_code == 200
    new_horizon_ids = {s["id"] for s in response.json()["new_horizons"]}
    assert "react" not in new_horizon_ids  # already recorded
    assert new_horizon_ids  # web_developer has other in-demand skills the user hasn't recorded


def test_career_translation_without_a_role_selected_has_no_role_data():
    headers = _new_session_headers()

    response = client.get("/api/v1/career-translation", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "role_label": None,
        "role_data_available": False,
        "owned_skills": [],
        "custom_skills": [],
        "new_horizons": [],
    }
