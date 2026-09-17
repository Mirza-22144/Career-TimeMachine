"""Predicted future role, from the AI team's trained career-role model."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

UNAVAILABLE = {"role_id": None, "role_label": None}


def _new_headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _save_profile(headers: dict[str, str], **overrides) -> None:
    body = {"role_id": "web_developer", "skill_ids": ["react", "git"], **overrides}
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200


def test_new_token_has_no_predicted_role():
    response = client.get("/api/v1/predicted-role", headers=_new_headers())

    assert response.status_code == 200
    assert response.json() == UNAVAILABLE


def test_fake_test_only_role_gets_no_prediction():
    # "software_engineer" only exists in the fixed test catalogue, not in
    # the real trained model's 27 supported roles - the service must fail
    # closed (nulls), not surface the model's internal error.
    headers = _new_headers()
    _save_profile(headers, role_id="software_engineer", skill_ids=["python"])

    response = client.get("/api/v1/predicted-role", headers=headers)

    assert response.status_code == 200
    assert response.json() == UNAVAILABLE


def test_real_role_gets_a_real_prediction():
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=["react", "git"])

    response = client.get("/api/v1/predicted-role", headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert body["role_id"] is not None
    assert body["role_label"] is not None
    # The model never re-recommends the role she is predicting from.
    assert body["role_id"] != "web_developer"
    # The model never predicts the catch-all "other" role.
    assert body["role_id"] != "other"


def test_other_previous_role_still_gets_a_prediction():
    headers = _new_headers()
    _save_profile(headers, role_id="other", role_other_text="Mainframe Specialist", skill_ids=["python"])

    response = client.get("/api/v1/predicted-role", headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert body["role_id"] is not None
    assert body["role_id"] != "other"


def test_prediction_does_not_require_a_confirmed_profile():
    # Your Direction shows the predicted role before the wizard is
    # finished, so this must not require profile.confirmed like starting
    # practice does.
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=[])

    response = client.get("/api/v1/predicted-role", headers=headers)

    assert response.status_code == 200
    assert response.json()["role_id"] is not None


def test_one_token_cannot_see_another_tokens_prediction():
    headers_a = _new_headers()
    headers_b = _new_headers()
    _save_profile(headers_a, role_id="web_developer", skill_ids=["react"])

    response_b = client.get("/api/v1/predicted-role", headers=headers_b)

    assert response_b.json() == UNAVAILABLE


def test_predicted_role_requires_a_valid_token():
    response = client.get("/api/v1/predicted-role", headers={"X-Session-Token": "not-a-real-token"})

    assert response.status_code == 401
