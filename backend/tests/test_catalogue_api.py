from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_roles_returns_list():
    r = client.get("/api/v1/catalogue/roles")
    assert r.status_code == 200
    assert any(i["id"] == "software_engineer" for i in r.json())


def test_experience_options_include_ten_plus():
    r = client.get("/api/v1/catalogue/experience-options")
    assert "10_plus" in [i["id"] for i in r.json()]


def test_break_reasons_include_prefer_not_to_say():
    r = client.get("/api/v1/catalogue/break-reasons")
    assert "prefer_not_to_say" in [i["id"] for i in r.json()]