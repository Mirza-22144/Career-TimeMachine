"""Rate limiting on session creation and response submission (pen-test H-4).

Offline: the limiter counts in memory and TestClient sets the client
address, so no real network or IP infrastructure is involved.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python"],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}
SETTINGS = {"duration": "quick", "difficulty": "standard"}
UNKNOWN_ID = "0" * 32

SESSION_LIMIT = 10
SUBMISSION_LIMIT = 30


def _assert_rate_limited(response) -> None:
    assert response.status_code == 429
    assert response.json() == {
        "error": {
            "code": "RATE_LIMITED",
            "message": "Too many requests. Please wait a minute and try again.",
            "details": [],
        }
    }
    assert response.headers["Retry-After"] == "60"
    # No limiter configuration or internals leak.
    for internal in ("per 1 minute", "slowapi", "limits", "Traceback"):
        assert internal not in response.text


def _new_headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _started_practice() -> tuple[dict[str, str], dict]:
    headers = _new_headers()
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    assert client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": "software_engineer", "source": "previous"},
    ).status_code == 200
    started = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)
    assert started.status_code == 201
    return headers, started.json()


def _unknown_session_response_path() -> str:
    return f"/api/v1/practice-sessions/{UNKNOWN_ID}/scenarios/{UNKNOWN_ID}/response"


def test_session_creation_under_the_limit_succeeds(rate_limiting_on):
    for _ in range(SESSION_LIMIT):
        response = client.post("/api/v1/anonymous-sessions")
        assert response.status_code == 201
        assert response.json()["token"]


def test_session_creation_over_the_limit_returns_429(rate_limiting_on):
    for _ in range(SESSION_LIMIT):
        assert client.post("/api/v1/anonymous-sessions").status_code == 201

    _assert_rate_limited(client.post("/api/v1/anonymous-sessions"))


def test_session_creation_limit_is_per_client_address(rate_limiting_on):
    for _ in range(SESSION_LIMIT + 1):
        client.post("/api/v1/anonymous-sessions")

    other_address = TestClient(app, client=("203.0.113.7", 50000))

    assert other_address.post("/api/v1/anonymous-sessions").status_code == 201


def test_response_submission_over_the_limit_returns_429(rate_limiting_on):
    headers = _new_headers()
    path = _unknown_session_response_path()
    body = {"selected_option_id": "option_a"}

    # Every call reaches the endpoint (valid token and body) and counts,
    # whatever the outcome.
    for _ in range(SUBMISSION_LIMIT):
        assert client.post(path, headers=headers, json=body).status_code == 404

    _assert_rate_limited(client.post(path, headers=headers, json=body))


def test_normal_practice_submission_is_unaffected(rate_limiting_on):
    headers, session = _started_practice()
    scenario = session["scenarios"][0]
    path = (
        f"/api/v1/practice-sessions/{session['session_id']}"
        f"/scenarios/{scenario['scenario_id']}/response"
    )

    response = client.post(
        path, headers=headers, json={"selected_option_id": scenario["options"][0]["option_id"]}
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/anonymous-sessions/current"),
        ("get", "/api/v1/profile"),
        ("get", "/api/v1/catalogue/roles"),
    ],
)
def test_other_endpoints_are_not_rate_limited(rate_limiting_on, method, path):
    headers = _new_headers()

    for _ in range(SUBMISSION_LIMIT + 5):
        assert getattr(client, method)(path, headers=headers).status_code == 200


def test_limits_are_counted_per_endpoint(rate_limiting_on):
    headers = _new_headers()
    for _ in range(SESSION_LIMIT):
        client.post("/api/v1/anonymous-sessions")
    _assert_rate_limited(client.post("/api/v1/anonymous-sessions"))

    response = client.post(
        _unknown_session_response_path(), headers=headers, json={"selected_option_id": "option_a"}
    )

    assert response.status_code == 404
