"""Job-description extraction (Iteration 3, BE 3.2; AI Task 1 / AI 3.1)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import HAS_JOB_DESCRIPTION_MODEL
from app.main import app
from app.providers.job_description_extraction_provider import (
    JobDescriptionExtractionProvider,
    JobDescriptionExtractionProviderError,
)
from app.providers.unavailable_job_description_extraction_provider import (
    UnavailableJobDescriptionExtractionProvider,
)

client = TestClient(app)

RAW_TEXT = (
    "We are looking for a Data Engineer with Python and AWS experience. "
    "You will develop data pipelines and maintain cloud data services. "
    "Minimum 3 years of experience required. Strong communication skills needed."
)

VALID_RESULT = {
    "skills": [
        {"label": "Python", "category": "technical"},
        {"label": "AWS", "category": "technical"},
        {"label": "Communication", "category": "soft"},
    ],
    "responsibilities": ["Develop data pipelines", "Maintain cloud data services"],
    "min_years_experience": 3,
    "keywords": ["Python", "AWS", "Communication"],
    "role_title_guess": "Data Engineer",
}


class FakeProvider(JobDescriptionExtractionProvider):
    """Returns a fixed, valid extraction result - the test double every
    success-path test uses via use_job_description_provider."""

    def extract(self, request):
        return dict(VALID_RESULT)


class FailingProvider(JobDescriptionExtractionProvider):
    def extract(self, request):
        raise JobDescriptionExtractionProviderError("provider is down")


class InvalidResultProvider(JobDescriptionExtractionProvider):
    """Returns something that doesn't match JobDescriptionExtractionContent -
    an extra field, matching the "no field beyond what was agreed" rule."""

    def extract(self, request):
        return {**VALID_RESULT, "confidence_score": 0.9}


def _new_token() -> str:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return response.json()["token"]


def _headers(token: str | None = None) -> dict[str, str]:
    return {"X-Session-Token": token or _new_token()}


def test_create_job_description_extracts_and_saves(use_job_description_provider):
    use_job_description_provider(FakeProvider())
    headers = _headers()

    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})

    assert response.status_code == 201
    body = response.json()
    assert body["raw_text"] == RAW_TEXT
    assert body["extracted_skills"] == VALID_RESULT["skills"]
    assert body["extracted_responsibilities"] == VALID_RESULT["responsibilities"]
    assert body["min_years_experience"] == 3
    assert body["keywords"] == VALID_RESULT["keywords"]
    assert body["role_title_guess"] == "Data Engineer"
    assert body["job_description_id"]
    assert body["created_at"]


def test_create_job_description_requires_a_token():
    response = client.post("/api/v1/job-descriptions", json={"raw_text": RAW_TEXT})
    assert response.status_code == 401


def test_create_job_description_rejects_empty_text():
    headers = _headers()
    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": ""})
    assert response.status_code == 422


def test_create_job_description_rejects_text_under_150_characters():
    """AC 5.1.1's exception condition - the frontend enforces this before
    submitting, this is the real backend backstop."""
    headers = _headers()
    too_short = "Short job ad text, well under the real minimum length."
    assert len(too_short) < 150
    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": too_short})
    assert response.status_code == 422


def test_create_job_description_rejects_oversized_text():
    headers = _headers()
    too_long = "a" * 20001
    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": too_long})
    assert response.status_code == 422


def test_create_job_description_rejects_unknown_fields():
    headers = _headers()
    response = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"raw_text": RAW_TEXT, "years_experience": "5"},
    )
    assert response.status_code == 422


def test_create_job_description_handles_provider_failure(use_job_description_provider):
    use_job_description_provider(FailingProvider())
    headers = _headers()

    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "JOB_DESCRIPTION_EXTRACTION_UNAVAILABLE",
            "message": "We couldn't analyse your job description. Please try again.",
            "details": [],
        }
    }


def test_create_job_description_fails_without_a_real_model_configured(use_job_description_provider):
    """Explicitly simulates the model being unavailable, rather than relying
    on dependencies.py's default wiring - whether the real ~1.3GB model
    happens to be present on the machine running this suite is local
    environment state, not something a test should depend on (same
    principle as fake_catalogue/fake_session_and_profile_stores)."""
    use_job_description_provider(UnavailableJobDescriptionExtractionProvider())
    headers = _headers()
    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "JOB_DESCRIPTION_EXTRACTION_UNAVAILABLE"


@pytest.mark.skipif(
    not HAS_JOB_DESCRIPTION_MODEL,
    reason="real GLiNER model not present locally - see MODEL_DEPLOYMENT.md",
)
def test_create_job_description_with_the_real_model():
    """Runs only where the real ~1.3GB model is actually present (this
    machine, and eventually CI/Cloud Run once it's part of the deployed
    environment) - everywhere else it's skipped rather than failed, so the
    regular offline suite never depends on it. Not exact-match (the model's
    output isn't pinned to a fixed string), just a shape/sanity check that
    the real pipeline still produces valid, non-empty output end to end."""
    headers = _headers()
    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})
    assert response.status_code == 201
    body = response.json()
    assert body["extracted_skills"]
    assert any(skill["label"].lower() == "python" for skill in body["extracted_skills"])
    assert body["min_years_experience"] == 3


def test_create_job_description_rejects_invalid_provider_output(use_job_description_provider):
    use_job_description_provider(InvalidResultProvider())
    headers = _headers()

    response = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "JOB_DESCRIPTION_EXTRACTION_UNAVAILABLE"


def test_get_job_description_returns_the_saved_record(use_job_description_provider):
    use_job_description_provider(FakeProvider())
    headers = _headers()
    created = client.post(
        "/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT}
    ).json()

    response = client.get(f"/api/v1/job-descriptions/{created['job_description_id']}", headers=headers)

    assert response.status_code == 200
    assert response.json() == created


def test_get_job_description_404s_for_unknown_id():
    headers = _headers()
    response = client.get("/api/v1/job-descriptions/does-not-exist", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_DESCRIPTION_NOT_FOUND"


def test_get_job_description_does_not_leak_across_owners(use_job_description_provider):
    use_job_description_provider(FakeProvider())
    owner_a_headers = _headers()
    owner_b_headers = _headers()
    created = client.post(
        "/api/v1/job-descriptions", headers=owner_a_headers, json={"raw_text": RAW_TEXT}
    ).json()

    response = client.get(
        f"/api/v1/job-descriptions/{created['job_description_id']}", headers=owner_b_headers
    )

    assert response.status_code == 404


def test_list_job_descriptions_returns_all_for_the_owner_newest_first(use_job_description_provider):
    use_job_description_provider(FakeProvider())
    headers = _headers()
    first = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT}).json()
    second = client.post(
        "/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT + " Second posting."}
    ).json()

    response = client.get("/api/v1/job-descriptions", headers=headers)

    assert response.status_code == 200
    ids = [jd["job_description_id"] for jd in response.json()]
    assert ids == [second["job_description_id"], first["job_description_id"]]


def test_list_job_descriptions_is_empty_for_a_new_owner():
    headers = _headers()
    response = client.get("/api/v1/job-descriptions", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_delete_job_description_removes_it(use_job_description_provider):
    """AC 3.5.1."""
    use_job_description_provider(FakeProvider())
    headers = _headers()
    created = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT}).json()

    delete_response = client.delete(f"/api/v1/job-descriptions/{created['job_description_id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/job-descriptions/{created['job_description_id']}", headers=headers)
    assert get_response.status_code == 404


def test_delete_job_description_404s_for_unknown_id():
    headers = _headers()
    response = client.delete("/api/v1/job-descriptions/does-not-exist", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_DESCRIPTION_NOT_FOUND"


def test_delete_job_description_does_not_cross_owners(use_job_description_provider):
    use_job_description_provider(FakeProvider())
    owner_a_headers = _headers()
    owner_b_headers = _headers()
    created = client.post(
        "/api/v1/job-descriptions", headers=owner_a_headers, json={"raw_text": RAW_TEXT}
    ).json()

    response = client.delete(
        f"/api/v1/job-descriptions/{created['job_description_id']}", headers=owner_b_headers
    )
    assert response.status_code == 404

    still_there = client.get(
        f"/api/v1/job-descriptions/{created['job_description_id']}", headers=owner_a_headers
    )
    assert still_there.status_code == 200


def test_delete_job_description_requires_a_token():
    response = client.delete("/api/v1/job-descriptions/does-not-exist")
    assert response.status_code == 401
