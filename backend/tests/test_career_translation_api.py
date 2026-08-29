from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_session_headers() -> dict[str, str]:
    """Create an anonymous session and return the protected-route header."""
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def test_career_translation_returns_all_selected_catalogue_skill_mappings():
    headers = _new_session_headers()
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "skill_ids": ["rest_apis", "react", "docker"],
            "custom_skills": ["Release coordination"],
        },
    )
    assert patch_response.status_code == 200

    response = client.get("/api/v1/career-translation", headers=headers)

    assert response.status_code == 200
    assert response.json() == [
        {
            "previous_skill": {"id": "rest_apis", "name": "REST APIs"},
            "connected_areas": [
                {
                    "id": "cloud_native_engineering",
                    "name": "Cloud-Native Engineering",
                }
            ],
        },
        {
            "previous_skill": {"id": "react", "name": "React"},
            "connected_areas": [],
        },
        {
            "previous_skill": {"id": "docker", "name": "Docker"},
            "connected_areas": [
                {
                    "id": "modern_devops",
                    "name": "Modern DevOps Practices",
                },
                {
                    "id": "cloud_native_engineering",
                    "name": "Cloud-Native Engineering",
                },
            ],
        },
    ]


def test_career_translation_returns_empty_list_when_no_skills_selected():
    headers = _new_session_headers()

    response = client.get("/api/v1/career-translation", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_single_skill_translation_returns_selected_skill_mapping():
    headers = _new_session_headers()
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"skill_ids": ["python", "java"]},
    )
    assert patch_response.status_code == 200

    response = client.get("/api/v1/career-translation/python", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "previous_skill": {"id": "python", "name": "Python"},
        "connected_areas": [
            {
                "id": "data_analytics_basics",
                "name": "Data & Analytics Basics",
            }
        ],
    }


def test_single_skill_translation_404s_when_skill_not_selected():
    headers = _new_session_headers()
    patch_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"skill_ids": ["python"]},
    )
    assert patch_response.status_code == 200

    response = client.get("/api/v1/career-translation/rest_apis", headers=headers)

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "HTTP_404",
            "message": "skill not selected",
            "details": [],
        }
    }
