"""Two predicted future roles with market data (Iteration 3, BE 3.4;
AI 3.2's Version 2 model; DB 3.1's real Australian vacancy data)."""

from datetime import date

from fastapi.testclient import TestClient

from app.api import dependencies
from app.main import app
from app.repositories.interfaces.vacancy_repository import NATIONAL_STATE, RoleMarketData
from app.repositories.memory.memory_vacancy_repository import MemoryVacancyRepository

client = TestClient(app)

EMPTY = {"predicted_roles": []}


def _new_headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _save_profile(headers: dict[str, str], **overrides) -> None:
    body = {"role_id": "web_developer", "skill_ids": ["react", "git"], **overrides}
    assert client.patch("/api/v1/profile", headers=headers, json=body).status_code == 200


def test_new_token_has_no_predicted_roles():
    response = client.get("/api/v1/predicted-roles", headers=_new_headers())

    assert response.status_code == 200
    assert response.json() == EMPTY


def test_fake_test_only_role_gets_no_predictions():
    headers = _new_headers()
    _save_profile(headers, role_id="software_engineer", skill_ids=["python"])

    response = client.get("/api/v1/predicted-roles", headers=headers)

    assert response.status_code == 200
    assert response.json() == EMPTY


def test_real_role_gets_two_distinct_real_predictions():
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=["react", "git"])

    response = client.get("/api/v1/predicted-roles", headers=headers)

    assert response.status_code == 200
    roles = response.json()["predicted_roles"]
    assert len(roles) == 2
    role_ids = [r["role_id"] for r in roles]
    assert len(set(role_ids)) == 2  # distinct
    assert "web_developer" not in role_ids  # never re-recommends her current role
    assert "other" not in role_ids
    for role in roles:
        assert role["role_id"]
        assert role["role_label"]
        assert "market_data" in role  # present, even if null


def test_predictions_have_no_market_data_without_a_mapping():
    """Default test wiring (MemoryVacancyRepository, empty) - matches a
    role with no ANZSCO mapping yet against the real database."""
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=["react", "git"])

    response = client.get("/api/v1/predicted-roles", headers=headers)

    for role in response.json()["predicted_roles"]:
        assert role["market_data"] is None


def test_predictions_include_real_market_data_when_a_mapping_exists(monkeypatch):
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=["react", "git"])

    # Discover what the real model actually predicts first, then inject
    # market data for exactly those roles - keeps this independent of which
    # two roles the model happens to pick.
    predicted = client.get("/api/v1/predicted-roles", headers=headers).json()["predicted_roles"]
    first_role_id = predicted[0]["role_id"]
    market_data = RoleMarketData(
        anzsco_code="2612",
        anzsco_title="Multimedia Specialists and Web Developers",
        confidence="high",
        state=NATIONAL_STATE,
        latest_month=date(2026, 8, 1),
        ads_latest=1500,
        ads_12m_avg=1400,
        yoy_change_pct=12.5,
    )
    monkeypatch.setattr(
        dependencies,
        "_vacancy_repository",
        MemoryVacancyRepository({(first_role_id, NATIONAL_STATE): market_data}),
    )

    response = client.get("/api/v1/predicted-roles", headers=headers)

    assert response.status_code == 200
    roles = {r["role_id"]: r for r in response.json()["predicted_roles"]}
    assert roles[first_role_id]["market_data"] == {
        "anzsco_code": "2612",
        "anzsco_title": "Multimedia Specialists and Web Developers",
        "confidence": "high",
        "state": "AUST",
        "latest_month": "2026-08-01",
        "ads_latest": 1500,
        "ads_12m_avg": 1400,
        "yoy_change_pct": 12.5,
        "source": "Jobs and Skills Australia - Internet Vacancy Index",
    }


def test_predictions_do_not_require_a_confirmed_profile():
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=[])

    response = client.get("/api/v1/predicted-roles", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["predicted_roles"]) == 2


def test_one_token_cannot_see_another_tokens_predictions():
    headers_a = _new_headers()
    headers_b = _new_headers()
    _save_profile(headers_a, role_id="web_developer", skill_ids=["react"])

    response_b = client.get("/api/v1/predicted-roles", headers=headers_b)

    assert response_b.json() == EMPTY


def test_predicted_roles_requires_a_valid_token():
    response = client.get("/api/v1/predicted-roles", headers={"X-Session-Token": "not-a-real-token"})

    assert response.status_code == 401


def test_existing_singular_endpoint_is_unaffected():
    """BE 3.4 is additive - GET /predicted-role (singular) must keep
    working exactly as before for the current frontend."""
    headers = _new_headers()
    _save_profile(headers, role_id="web_developer", skill_ids=["react", "git"])

    response = client.get("/api/v1/predicted-role", headers=headers)

    assert response.status_code == 200
    assert response.json()["role_id"] is not None
