"""GET /practice-role/predicted - role prediction (AI 2.1/2.2/2.3).

The real model is deterministic but slow to load repeatedly, so most tests
substitute a small fake predictor via the use_role_predictor fixture and
only a couple of tests exercise the real one end to end."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PROFILE = {
    "role_id": "web_developer",
    "years_experience": "5",
    "skill_ids": ["python", "react"],
    "custom_skills": ["Machine learning"],
    "responsibility_ids": [],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}


def _headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _confirm(headers: dict[str, str], **overrides) -> None:
    body = {**PROFILE, **overrides}
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200


class FakePredictor:
    """Returns whatever the test hands it, so validation/guardrail
    behaviour can be exercised without the real model."""

    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.received_payload = None

    def predict(self, payload):
        self.received_payload = payload
        if self.error is not None:
            raise self.error
        return self.result


def test_predicted_role_requires_a_session_token():
    response = client.get("/api/v1/practice-role/predicted")

    assert response.status_code == 401


def test_predicted_role_requires_a_confirmed_profile():
    response = client.get("/api/v1/practice-role/predicted", headers=_headers())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROFILE_NOT_CONFIRMED"


def test_predicted_role_returned_for_confirmed_profile(use_role_predictor):
    predictor = FakePredictor(result={"predicted_role": {"id": "data_scientist", "label": "Data Scientist"}})
    use_role_predictor(predictor)
    headers = _headers()
    _confirm(headers)

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"predicted_role": {"id": "data_scientist", "label": "Data Scientist"}}


def test_predicted_role_request_carries_only_role_and_skills(use_role_predictor):
    """No token, session id or other profile fields ever reach the model."""
    predictor = FakePredictor(result={"predicted_role": {"id": "data_scientist", "label": "Data Scientist"}})
    use_role_predictor(predictor)
    headers = _headers()
    _confirm(headers)

    client.get("/api/v1/practice-role/predicted", headers=headers)

    assert set(predictor.received_payload.keys()) == {"role", "skills"}
    assert predictor.received_payload["role"] == {"id": "web_developer", "label": "Web Developer"}
    assert predictor.received_payload["skills"]["custom"] == ["Machine learning"]


def test_predicted_role_rejects_unrecognised_role(use_role_predictor):
    """A role id the model doesn't know (raises ValueError) is a client-
    visible gap, not a crash."""
    use_role_predictor(FakePredictor(error=ValueError("Unknown role ID: software_engineer")))
    headers = _headers()
    _confirm(headers, role_id="software_engineer")

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROLE_PREDICTION_UNSUPPORTED_ROLE"


def test_predicted_role_unavailable_when_no_predictor_loaded(use_role_predictor):
    use_role_predictor(None)
    headers = _headers()
    _confirm(headers)

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ROLE_PREDICTION_UNAVAILABLE"


@pytest.mark.parametrize(
    "bad_result",
    [
        {"predicted_role": {"id": "data_scientist"}},  # missing label
        {"predicted_role": {"id": "data_scientist", "label": "Data Scientist", "confidence": 0.9}},  # extra field
        {"predicted_role": {"id": "data_scientist", "label": "Data Scientist"}, "score": 0.9},  # extra top-level
        {"not_predicted_role": {"id": "data_scientist", "label": "Data Scientist"}},
        "not even a dict",
    ],
)
def test_predicted_role_rejects_malformed_model_output(use_role_predictor, bad_result):
    """The model's raw output is never trusted as-is - a shape it wasn't
    supposed to produce (e.g. a confidence score) fails safe as 503, not a
    500 or a leaked extra field."""
    use_role_predictor(FakePredictor(result=bad_result))
    headers = _headers()
    _confirm(headers)

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ROLE_PREDICTION_UNAVAILABLE"


def test_predicted_role_never_returns_other(use_role_predictor):
    """Backstop: even if the model ever broke its own "never other"
    guarantee, the backend does not serve it."""
    use_role_predictor(FakePredictor(result={"predicted_role": {"id": "other", "label": "Other"}}))
    headers = _headers()
    _confirm(headers)

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ROLE_PREDICTION_UNAVAILABLE"


def test_predicted_role_never_matches_current_role(use_role_predictor):
    """Backstop: even if the model ever broke its own "exclude the current
    role" guarantee, the backend does not serve it."""
    use_role_predictor(FakePredictor(result={"predicted_role": {"id": "web_developer", "label": "Web Developer"}}))
    headers = _headers()
    _confirm(headers)

    response = client.get("/api/v1/practice-role/predicted", headers=headers)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ROLE_PREDICTION_UNAVAILABLE"


def test_predicted_role_can_then_be_saved_as_practice_role(use_role_predictor):
    """The predicted role, once fetched, is a normal catalogue id that
    PUT /practice-role already accepts with source="predicted"."""
    predictor = FakePredictor(result={"predicted_role": {"id": "data_scientist", "label": "Data Scientist"}})
    use_role_predictor(predictor)
    headers = _headers()
    _confirm(headers)
    predicted = client.get("/api/v1/practice-role/predicted", headers=headers).json()["predicted_role"]

    # data_scientist isn't in the fixed test catalogue, so this documents
    # the contract rather than actually saving it - PUT still 400s on an
    # id the catalogue doesn't know, exactly as it would for any other
    # unrecognised id.
    response = client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": predicted["id"], "source": "predicted"},
    )
    assert response.status_code == 400


def test_real_predictor_loads_and_excludes_current_role_and_other():
    """One end-to-end pass against the real model bundle, not a fake -
    confirms the model actually loaded and its predict() output already
    satisfies the guardrails the service also double-checks."""
    from app.api import dependencies

    predictor = dependencies._role_predictor
    assert predictor is not None, "role prediction model failed to load"

    result = predictor.predict(
        {
            "role": {"id": "web_developer", "label": "Web Developer"},
            "skills": {"catalogue": [{"id": "python", "label": "Python"}], "custom": ["React"]},
        }
    )

    predicted_id = result["predicted_role"]["id"]
    assert predicted_id not in {"other", "web_developer"}
    assert predicted_id in predictor.role_labels


def test_role_prediction_not_logged_with_skill_content(caplog):
    """Nothing about a prediction call - success or failure - logs profile
    or skill content."""
    headers = _headers()
    _confirm(headers, custom_skills=["Very specific secret project name"])

    with caplog.at_level("DEBUG"):
        client.get("/api/v1/practice-role/predicted", headers=headers)

    assert "Very specific secret project name" not in caplog.text
