"""Profile-vs-job comparison and closest roles (AC 5.2.1 / 5.2.2)."""

from fastapi.testclient import TestClient

from app.main import app
from app.providers.job_description_extraction_provider import JobDescriptionExtractionProvider

client = TestClient(app)

RAW_TEXT = "x" * 150


class FakeProvider(JobDescriptionExtractionProvider):
    def __init__(self, title="Web Developer", years=3):
        self.title = title
        self.years = years

    def extract(self, request):
        return {
            "skills": [
                {"label": "React", "category": "technical"},
                {"label": "Git workflows", "category": "technical"},
                {"label": "Kubernetes", "category": "technical"},
                {"label": "Incident reviews", "category": "technical"},
            ],
            "responsibilities": ["Review pull requests and give feedback"],
            "min_years_experience": self.years,
            "keywords": [],
            "role_title_guess": self.title,
        }


def _setup(use_job_description_provider, provider=None, **profile):
    use_job_description_provider(provider or FakeProvider())
    token = client.post("/api/v1/anonymous-sessions").json()["token"]
    headers = {"X-Session-Token": token}
    body = {
        "role_id": "web_developer",
        "years_experience": "5",
        "skill_ids": ["react", "git"],
        "custom_responsibilities": ["Code review"],
        "break_started_on": "2021-01-01",
        **profile,
    }
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200
    created = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT})
    assert created.status_code == 201
    return headers, created.json()["job_description_id"]


def test_comparison_puts_each_requirement_in_one_group(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider)

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/comparison", headers=headers).json()

    assert body["skills_bring_back"] == ["React"]
    assert body["worth_refreshing"] == [{"requirement": "Git workflows", "profile_skill": "Git"}]
    assert body["transferable_experience"] == [
        {
            "experience": "Code review",
            "relates_to": "Review pull requests and give feedback",
            "explanation": "Code review relates to review pull requests and give feedback.",
        }
    ]
    assert body["skills_could_explore"] == ["Kubernetes", "Incident reviews"]
    assert body["break_start_year"] == 2021
    assert body["job_title"] == "Web Developer"
    assert body["experience_sentence"] == (
        "This role asks for 3 years of experience. Your profile shows 5 years as a Web Developer."
    )


def test_comparison_leaves_out_the_experience_sentence_when_no_years_stated(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider, FakeProvider(years=None))

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/comparison", headers=headers).json()

    assert body["experience_sentence"] is None


def test_comparison_has_no_score_or_verdict_fields(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider)

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/comparison", headers=headers).json()

    assert not {"score", "match", "percentage", "verdict"} & set(body)


def test_exact_title_is_reported_and_listed_first(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider)

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/closest-roles", headers=headers).json()

    assert body["exact_role_id"] == "web_developer"
    assert body["closest"][0] == {"role_id": "web_developer", "role_label": "Web Developer"}
    assert len(body["closest"]) <= 3
    assert "other" not in [role["role_id"] for role in body["closest"]]


def test_near_title_has_no_exact_role_but_still_finds_close_ones(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider, FakeProvider(title="Senior Software Engineer, Payments"))

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/closest-roles", headers=headers).json()

    assert body["exact_role_id"] is None
    assert body["closest"][0]["role_id"] == "software_engineer"


def test_unrelated_title_has_no_close_roles(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider, FakeProvider(title="Pastry Chef"))

    body = client.get(f"/api/v1/job-descriptions/{jd_id}/closest-roles", headers=headers).json()

    assert body == {"job_title": "Pastry Chef", "exact_role_id": None, "closest": [], "chosen_role_id": None}


def test_chosen_role_is_remembered_per_job_description(use_job_description_provider):
    headers, first_id = _setup(use_job_description_provider)
    second_id = client.post("/api/v1/job-descriptions", headers=headers, json={"raw_text": RAW_TEXT}).json()[
        "job_description_id"
    ]

    saved = client.put(
        f"/api/v1/job-descriptions/{first_id}/closest-role", headers=headers, json={"role_id": "data_analyst"}
    )

    assert saved.status_code == 204
    first = client.get(f"/api/v1/job-descriptions/{first_id}/closest-roles", headers=headers).json()
    second = client.get(f"/api/v1/job-descriptions/{second_id}/closest-roles", headers=headers).json()
    assert first["chosen_role_id"] == "data_analyst"
    assert second["chosen_role_id"] is None


def test_choosing_an_invalid_or_other_role_is_rejected(use_job_description_provider):
    headers, jd_id = _setup(use_job_description_provider)
    path = f"/api/v1/job-descriptions/{jd_id}/closest-role"

    assert client.put(path, headers=headers, json={"role_id": "not_a_role"}).status_code == 400
    assert client.put(path, headers=headers, json={"role_id": "other"}).status_code == 400


def test_choosing_a_role_for_another_owners_job_description_404s(use_job_description_provider):
    _headers, jd_id = _setup(use_job_description_provider)
    other = {"X-Session-Token": client.post("/api/v1/anonymous-sessions").json()["token"]}

    response = client.put(
        f"/api/v1/job-descriptions/{jd_id}/closest-role", headers=other, json={"role_id": "data_analyst"}
    )

    assert response.status_code == 404


def test_comparison_and_closest_roles_do_not_cross_owners(use_job_description_provider):
    _headers, jd_id = _setup(use_job_description_provider)
    other = {"X-Session-Token": client.post("/api/v1/anonymous-sessions").json()["token"]}

    assert client.get(f"/api/v1/job-descriptions/{jd_id}/comparison", headers=other).status_code == 404
    assert client.get(f"/api/v1/job-descriptions/{jd_id}/closest-roles", headers=other).status_code == 404


def test_a_role_chosen_outside_the_suggestions_appears_on_the_roadmap(use_job_description_provider):
    headers, _jd_id = _setup(use_job_description_provider)
    suggested = [r["role_id"] for r in client.get("/api/v1/roadmap", headers=headers).json()["suggested_roles"]]
    outside = next(r for r in ["software_engineer", "qa_engineer", "data_analyst"] if r not in suggested)

    client.put("/api/v1/practice-role", headers=headers, json={"role_id": outside, "source": "predicted"})
    roadmap = client.get("/api/v1/roadmap", headers=headers).json()

    assert roadmap["selected_role_id"] == outside
    assert roadmap["suggested_roles"][0]["role_id"] == outside
