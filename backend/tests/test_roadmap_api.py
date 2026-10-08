"""Your Roadmap (AC 2.2.3 / 2.2.4)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _save_profile(headers, **overrides) -> None:
    body = {"role_id": "web_developer", "years_experience": "5", "skill_ids": ["react", "git"], **overrides}
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200


def test_roadmap_is_empty_before_a_previous_role_is_saved():
    response = client.get("/api/v1/roadmap", headers=_headers())

    assert response.status_code == 200
    assert response.json() == {
        "previous_role": None,
        "years_experience_label": None,
        "suggested_roles": [],
        "selected_role_id": None,
        "chosen_roles": [],
    }


def test_roadmap_shows_previous_role_and_two_distinct_suggestions():
    headers = _headers()
    _save_profile(headers)

    body = client.get("/api/v1/roadmap", headers=headers).json()

    assert body["previous_role"]["role_id"] == "web_developer"
    assert body["years_experience_label"] == "5 years"
    assert {s["id"] for s in body["previous_role"]["skills_bring_back"]} == {"react", "git"}
    suggested_ids = [role["role_id"] for role in body["suggested_roles"]]
    assert len(suggested_ids) == 2
    assert len(set(suggested_ids)) == 2
    assert "web_developer" not in suggested_ids


def test_explore_skills_exclude_owned_skills_and_have_exactly_one_next():
    headers = _headers()
    _save_profile(headers)

    body = client.get("/api/v1/roadmap", headers=headers).json()

    for role in [body["previous_role"], *body["suggested_roles"]]:
        explore = role["skills_could_explore"]
        assert len(explore) <= 3
        assert not {s["id"] for s in explore} & {"react", "git"}
        if explore:
            assert [s["status"] for s in explore].count("next") == 1
            assert explore[0]["status"] == "next"


def test_selecting_a_role_to_practise_shows_on_the_roadmap():
    headers = _headers()
    _save_profile(headers)
    client.put("/api/v1/practice-role", headers=headers, json={"role_id": "web_developer", "source": "previous"})

    body = client.get("/api/v1/roadmap", headers=headers).json()

    assert body["selected_role_id"] == "web_developer"


def test_chosen_roles_keep_a_dated_history_newest_first():
    """AC 3.4.1: each role with the date chosen."""
    headers = _headers()
    _save_profile(headers)
    client.put("/api/v1/practice-role", headers=headers, json={"role_id": "web_developer", "source": "previous"})
    client.put("/api/v1/practice-role", headers=headers, json={"role_id": "data_analyst", "source": "predicted"})

    chosen = client.get("/api/v1/roadmap", headers=headers).json()["chosen_roles"]

    assert [role["role_id"] for role in chosen] == ["data_analyst", "web_developer"]
    assert chosen[0]["role_label"] == "Data Analyst"
    assert chosen[0]["chosen_at"]


def test_choosing_the_same_role_again_does_not_duplicate_it():
    headers = _headers()
    _save_profile(headers)
    for _ in range(2):
        client.put("/api/v1/practice-role", headers=headers, json={"role_id": "web_developer", "source": "previous"})

    chosen = client.get("/api/v1/roadmap", headers=headers).json()["chosen_roles"]

    assert [role["role_id"] for role in chosen] == ["web_developer"]


def test_roadmap_requires_a_valid_token():
    response = client.get("/api/v1/roadmap", headers={"X-Session-Token": "not-a-real-token"})

    assert response.status_code == 401
