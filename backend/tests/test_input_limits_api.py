"""Input caps on request bodies (pen-test H-1, H-2) and unknown-field
rejection. Every rejection is a 422 REQUEST_VALIDATION_ERROR that names the
field, saves nothing and does not echo the rejected value back."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _assert_rejected(response, field: str, error_type: str) -> None:
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "REQUEST_VALIDATION_ERROR"
    assert {"field": field, "type": error_type} in [
        {"field": d["field"], "type": d["type"]} for d in error["details"]
    ]


# H-1: free-text and id fields over their cap.
@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"role_other_text": "r" * 121}, "body.role_other_text"),
        ({"break_reason_other_text": "b" * 501}, "body.break_reason_other_text"),
        ({"role_id": "x" * 65}, "body.role_id"),
        ({"years_experience": "x" * 65}, "body.years_experience"),
        ({"break_reason": "x" * 65}, "body.break_reason"),
    ],
)
def test_profile_text_over_limit_is_rejected(body, field):
    headers = _headers()

    response = client.patch("/api/v1/profile", headers=headers, json=body)

    _assert_rejected(response, field, "string_too_long")
    assert list(body.values())[0] not in response.text


# H-2: a list item over its cap.
@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"custom_skills": ["Python", "s" * 121]}, "body.custom_skills.1"),
        ({"custom_responsibilities": ["r" * 301]}, "body.custom_responsibilities.0"),
        ({"skill_ids": ["python", "x" * 65]}, "body.skill_ids.1"),
        ({"responsibility_ids": ["x" * 65]}, "body.responsibility_ids.0"),
    ],
)
def test_profile_list_item_over_limit_is_rejected(body, field):
    response = client.patch("/api/v1/profile", headers=_headers(), json=body)

    _assert_rejected(response, field, "string_too_long")


# H-2: a list with too many items.
@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"skill_ids": ["python"] * 51}, "body.skill_ids"),
        ({"responsibility_ids": ["debugging"] * 51}, "body.responsibility_ids"),
        ({"custom_skills": [f"Skill {i}" for i in range(21)]}, "body.custom_skills"),
        ({"custom_responsibilities": [f"Task {i}" for i in range(21)]}, "body.custom_responsibilities"),
    ],
)
def test_profile_list_over_count_is_rejected(body, field):
    response = client.patch("/api/v1/profile", headers=_headers(), json=body)

    _assert_rejected(response, field, "too_long")


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"return_readiness": "x" * 65}, "body.return_readiness"),
        ({"area_to_explore": "x" * 65}, "body.area_to_explore"),
    ],
)
def test_career_direction_id_over_limit_is_rejected(body, field):
    response = client.patch("/api/v1/career-direction", headers=_headers(), json=body)

    _assert_rejected(response, field, "string_too_long")


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/api/v1/profile", {"role_id": "software_engineer", "confirmed": True}),
        ("patch", "/api/v1/career-direction", {"return_readiness": "ready", "is_admin": True}),
        ("put", "/api/v1/practice-role", {"role_id": "software_engineer", "source": "previous", "x": 1}),
        ("post", "/api/v1/practice-sessions", {"duration": "quick", "difficulty": "guided", "role_id": "qa"}),
    ],
)
def test_unknown_fields_are_rejected(method, path, body):
    extra_field = list(body)[-1]

    response = getattr(client, method)(path, headers=_headers(), json=body)

    _assert_rejected(response, f"body.{extra_field}", "extra_forbidden")


def test_rejected_update_saves_nothing():
    headers = _headers()
    assert client.patch(
        "/api/v1/profile", headers=headers, json={"custom_skills": ["Kept"]}
    ).status_code == 200

    rejected = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"custom_skills": ["New"], "role_other_text": "r" * 121},
    )

    assert rejected.status_code == 422
    assert client.get("/api/v1/profile", headers=headers).json()["custom_skills"] == ["Kept"]


def test_values_at_the_limits_are_accepted():
    headers = _headers()
    body = {
        "role_id": "other",
        "role_other_text": "r" * 120,
        "break_reason": "other",
        "break_reason_other_text": "b" * 500,
        "skill_ids": ["python"] * 50,
        "responsibility_ids": ["debugging"] * 50,
        "custom_skills": [f"{i:03d}" + "s" * 117 for i in range(20)],
        "custom_responsibilities": [f"{i:03d}" + "r" * 297 for i in range(20)],
    }

    response = client.patch("/api/v1/profile", headers=headers, json=body)

    assert response.status_code == 200
    profile = response.json()
    assert profile["role_other_text"] == "r" * 120
    assert profile["break_reason_other_text"] == "b" * 500
    assert len(profile["custom_skills"]) == 20
    assert len(profile["custom_responsibilities"]) == 20

    direction = client.patch(
        "/api/v1/career-direction",
        headers=headers,
        json={"return_readiness": "ready", "area_to_explore": "modern_devops"},
    )
    assert direction.status_code == 200


def test_existing_cleanup_of_free_text_is_unchanged():
    """Caps only; blanks are still dropped or cleared, not rejected."""
    headers = _headers()

    response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "role_other_text": "   ",
            "custom_skills": ["  Python  ", "", "python", "   "],
            "custom_responsibilities": [" Led releases "],
        },
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["role_other_text"] is None
    assert profile["custom_skills"] == ["Python"]
    assert profile["custom_responsibilities"] == ["Led releases"]


def test_padding_does_not_count_towards_text_limit():
    response = client.patch(
        "/api/v1/profile", headers=_headers(), json={"custom_skills": ["  " + "s" * 120 + "  "]}
    )

    assert response.status_code == 200
    assert response.json()["custom_skills"] == ["s" * 120]
