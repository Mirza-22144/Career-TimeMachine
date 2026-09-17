"""Startup storage-mode logging (pen-test R09) and security-event logging for
failed authentication and rate-limit rejections. Logs identify the event
only: no raw token, profile content or career-break details."""

import logging

import pytest
from fastapi.testclient import TestClient

from app import main
from app.core import config
from app.core.tokens import generate_token, hash_token
from app.main import app

client = TestClient(app)

BREAK_DETAIL = "Caring for my father after his surgery"
CUSTOM_SKILL = "Secret hobby project"
ROLE_TITLE = "Lighthouse keeper"
ANSWER = "My private written answer"
PROFILE = {
    "role_id": "other",
    "role_other_text": ROLE_TITLE,
    "years_experience": "5",
    "custom_skills": [CUSTOM_SKILL],
    "break_reason": "other",
    "break_reason_other_text": BREAK_DETAIL,
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}
UNKNOWN_ID = "0" * 32


def _security_events(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "app.security"]


def _assert_no_sensitive_data(caplog, token: str | None = None) -> None:
    for sensitive in (BREAK_DETAIL, CUSTOM_SKILL, ROLE_TITLE, ANSWER):
        assert sensitive not in caplog.text
    if token is not None:
        assert token not in caplog.text
        # Not the full stored hash either, only a short prefix at most.
        assert hash_token(token) not in caplog.text


def _new_token() -> str:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return response.json()["token"]


# R09: startup storage mode.


def test_startup_logs_in_memory_storage_mode(monkeypatch, caplog):
    monkeypatch.setattr(main, "HAS_DATABASE", False)

    with caplog.at_level(logging.INFO), TestClient(app):
        pass

    [record] = [r for r in caplog.records if "Storage mode" in r.getMessage()]
    assert record.levelno == logging.WARNING
    assert record.getMessage().startswith("Storage mode: in-memory")


def test_startup_logs_database_storage_mode_without_connection_details(monkeypatch, caplog):
    secrets = {
        "DB_HOST": "db-host.internal.example",
        "DB_NAME": "ctm_secret_db",
        "DB_USER": "ctm_admin_user",
        "DB_PASSWORD": "hunter2-db-password",
    }
    for name, value in secrets.items():
        monkeypatch.setattr(config, name, value)
    monkeypatch.setattr(main, "HAS_DATABASE", True)

    with caplog.at_level(logging.INFO), TestClient(app):
        pass

    [record] = [r for r in caplog.records if "Storage mode" in r.getMessage()]
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Storage mode: database (PostgreSQL)"
    for value in secrets.values():
        assert value not in caplog.text


# Failed authentication.


@pytest.mark.parametrize(
    ("headers", "reason"),
    [
        ({}, "missing_token"),
        ({"X-Session-Token": "not a token!"}, "malformed_token"),
        ({"X-Session-Token": generate_token()}, "unknown_token"),
    ],
)
def test_failed_authentication_is_logged_as_security_event(caplog, headers, reason):
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 401
    [event] = _security_events(caplog)
    assert event.startswith("security_event=auth_failed at=")
    assert "method=GET path=/api/v1/profile" in event
    assert event.endswith(f"reason={reason}")
    for presented in headers.values():
        assert presented not in caplog.text
        assert hash_token(presented) not in caplog.text


def test_failed_authentication_log_has_no_profile_data(caplog):
    token = _new_token()
    headers = {"X-Session-Token": token}
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    mistyped = token[:-1] + ("A" if token[-1] != "A" else "B")

    with caplog.at_level(logging.INFO):
        response = client.patch("/api/v1/profile", headers={"X-Session-Token": mistyped}, json=PROFILE)

    assert response.status_code == 401
    assert len(_security_events(caplog)) == 1
    _assert_no_sensitive_data(caplog, token)
    assert mistyped not in caplog.text


def test_successful_authentication_logs_no_security_event(caplog):
    token = _new_token()

    with caplog.at_level(logging.INFO):
        assert client.get("/api/v1/profile", headers={"X-Session-Token": token}).status_code == 200

    assert _security_events(caplog) == []


# Rate-limit rejections.


def test_session_creation_rate_limit_is_logged_as_security_event(rate_limiting_on, caplog):
    for _ in range(10):
        assert client.post("/api/v1/anonymous-sessions").status_code == 201
    assert _security_events(caplog) == []

    with caplog.at_level(logging.INFO):
        response = client.post("/api/v1/anonymous-sessions")

    assert response.status_code == 429
    [event] = _security_events(caplog)
    assert event.startswith("security_event=rate_limited at=")
    assert event.endswith("method=POST path=/api/v1/anonymous-sessions")
    assert "token" not in event


def test_response_submission_rate_limit_log_has_no_token_or_career_data(rate_limiting_on, caplog):
    token = _new_token()
    headers = {"X-Session-Token": token}
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    path = f"/api/v1/practice-sessions/{UNKNOWN_ID}/scenarios/{UNKNOWN_ID}/response"
    body = {"response_text": ANSWER}
    for _ in range(30):
        assert client.post(path, headers=headers, json=body).status_code == 404

    with caplog.at_level(logging.INFO):
        response = client.post(path, headers=headers, json=body)

    assert response.status_code == 429
    [event] = _security_events(caplog)
    assert event.startswith("security_event=rate_limited at=")
    assert f"method=POST path={path}" in event
    # Identifies the caller by a short prefix of the stored token hash only.
    assert event.endswith(f"token_hash_prefix={hash_token(token)[:12]}")
    _assert_no_sensitive_data(caplog, token)
