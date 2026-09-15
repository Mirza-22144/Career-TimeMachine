from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_then_fetch_session():
    r = client.post("/api/v1/anonymous-sessions")
    assert r.status_code == 201
    token = r.json()["token"]
    assert token                                   # non-empty token returned

    r2 = client.get("/api/v1/anonymous-sessions/current",
                    headers={"X-Session-Token": token})
    assert r2.status_code == 200
    assert r2.json()["created_at"] == r.json()["created_at"]  # same session comes back
    assert "token" not in r2.json()                # token is never echoed back


def test_current_without_token_is_401():
    response = client.get("/api/v1/anonymous-sessions/current")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "HTTP_401",
            "message": "Missing session token",
            "details": [],
        }
    }
