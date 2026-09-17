"""Database failures return controlled errors (LeanKit: Implement persistent
token access).

Every Postgres repository's pool is swapped for a fake that raises psycopg2
errors, so these run offline with no real database, like the rest of the
suite.
"""

import importlib
import logging
import sys
from datetime import datetime, timezone

import psycopg2
import psycopg2.pool
import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.main import app

client = TestClient(app)

# Driver messages can carry hosts, SQL and table names. None of it may reach
# the client.
LEAKY_DETAIL = 'could not connect to server on host "db.internal" (10.0.0.5): table profile_skill'

PROFILE = {
    "role_id": "software_engineer",
    "years_experience": "5",
    "skill_ids": ["python", "git"],
    "break_reason": "caregiving",
    "break_started_on": "2024-01-01",
    "planned_return_date": "2024-06-01",
}
SETTINGS = {"duration": "standard", "difficulty": "guided"}


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, sql, params=None):
        if self.connection.fails_on(sql):
            raise self.connection.error

    def fetchall(self):
        return list(self.connection.rows)


class FakeConnection:
    """Raises `error` for every statement `fails_on` matches; reads that
    don't fail return `rows`."""

    def __init__(self, error, fails_on=lambda sql: True, rows=()):
        self.error = error
        self.fails_on = fails_on
        self.rows = rows
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakePool:
    def __init__(self, connection=None, getconn_error=None):
        self.connection = connection
        self.getconn_error = getconn_error
        self.returned = []

    def getconn(self):
        if self.getconn_error is not None:
            raise self.getconn_error
        return self.connection

    def putconn(self, connection):
        self.returned.append(connection)


@pytest.fixture
def postgres_repository(monkeypatch):
    """Load a Postgres repository module without connecting (its pool is
    normally created at import time) and point it at a fake pool."""

    def _load(module_name, pool):
        full_name = f"app.repositories.postgres.{module_name}"
        if full_name not in sys.modules:
            with monkeypatch.context() as patch:
                patch.setattr(psycopg2.pool, "SimpleConnectionPool", lambda **kwargs: FakePool())
                importlib.import_module(full_name)
        module = sys.modules[full_name]
        monkeypatch.setattr(module, "_pool", pool)
        return module

    return _load


def _headers() -> dict[str, str]:
    response = client.post("/api/v1/anonymous-sessions")
    assert response.status_code == 201
    return {"X-Session-Token": response.json()["token"]}


def _assert_database_unavailable(response) -> None:
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "DATABASE_UNAVAILABLE",
            "message": "We couldn't complete your request. Please try again.",
            "details": [],
        }
    }
    assert "db.internal" not in response.text
    assert "profile_skill" not in response.text
    assert "Traceback" not in response.text


def test_creating_session_when_database_is_unreachable_returns_controlled_error(
    postgres_repository, monkeypatch, caplog
):
    pool = FakePool(getconn_error=psycopg2.OperationalError(LEAKY_DETAIL))
    module = postgres_repository("postgres_session_repository", pool)
    monkeypatch.setattr(dependencies, "_session_repository", module.PostgresSessionRepository())

    with caplog.at_level(logging.ERROR):
        response = client.post("/api/v1/anonymous-sessions")

    _assert_database_unavailable(response)
    # The original failure is still logged server-side.
    assert "OperationalError" in caplog.text


def test_token_check_when_pool_is_exhausted_returns_controlled_error(
    postgres_repository, monkeypatch
):
    headers = _headers()
    pool = FakePool(getconn_error=psycopg2.pool.PoolError("connection pool exhausted"))
    module = postgres_repository("postgres_session_repository", pool)
    monkeypatch.setattr(dependencies, "_session_repository", module.PostgresSessionRepository())

    response = client.get("/api/v1/profile", headers=headers)

    _assert_database_unavailable(response)
    assert "exhausted" not in response.text


def test_session_touch_failure_rolls_back_and_returns_controlled_error(
    postgres_repository, monkeypatch
):
    headers = _headers()
    now = datetime.now(timezone.utc)
    connection = FakeConnection(
        psycopg2.OperationalError(LEAKY_DETAIL),
        fails_on=lambda sql: sql.startswith("UPDATE"),
        rows=[(now, now)],
    )
    pool = FakePool(connection)
    module = postgres_repository("postgres_session_repository", pool)
    monkeypatch.setattr(dependencies, "_session_repository", module.PostgresSessionRepository())

    response = client.get("/api/v1/profile", headers=headers)

    _assert_database_unavailable(response)
    assert connection.rolled_back
    assert not connection.committed
    assert connection in pool.returned


def test_profile_read_failure_returns_controlled_error_and_releases_connection(
    postgres_repository, monkeypatch
):
    headers = _headers()
    connection = FakeConnection(psycopg2.OperationalError(LEAKY_DETAIL))
    pool = FakePool(connection)
    module = postgres_repository("postgres_profile_repository", pool)
    monkeypatch.setattr(dependencies, "_profile_repository", module.PostgresProfileRepository())

    response = client.get("/api/v1/profile", headers=headers)

    _assert_database_unavailable(response)
    # Rolled back first, so the pooled connection isn't left in an aborted
    # transaction for the next request.
    assert connection.rolled_back
    assert pool.returned == [connection]


def test_profile_save_failure_rolls_back_and_returns_controlled_error(
    postgres_repository, monkeypatch
):
    headers = _headers()
    connection = FakeConnection(
        psycopg2.IntegrityError(LEAKY_DETAIL), fails_on=lambda sql: "INSERT" in sql
    )
    pool = FakePool(connection)
    module = postgres_repository("postgres_profile_repository", pool)
    monkeypatch.setattr(dependencies, "_profile_repository", module.PostgresProfileRepository())

    response = client.patch("/api/v1/profile", headers=headers, json=PROFILE)

    _assert_database_unavailable(response)
    assert connection.rolled_back
    assert not connection.committed
    assert connection in pool.returned


def test_non_database_error_in_transaction_is_not_reported_as_database_unavailable(
    postgres_repository,
):
    connection = FakeConnection(psycopg2.OperationalError(LEAKY_DETAIL), fails_on=lambda sql: False)
    module = postgres_repository("postgres_profile_repository", FakePool(connection))

    def _buggy(cur):
        raise ValueError("a bug, not a database failure")

    with pytest.raises(ValueError):
        module._run_in_transaction(_buggy)
    assert connection.rolled_back


def test_practice_session_read_failure_returns_controlled_error(postgres_repository, monkeypatch):
    headers = _headers()
    pool = FakePool(getconn_error=psycopg2.OperationalError(LEAKY_DETAIL))
    module = postgres_repository("postgres_practice_session_repository", pool)
    monkeypatch.setattr(
        dependencies, "_practice_session_repository", module.PostgresPracticeSessionRepository()
    )

    response = client.get("/api/v1/practice-sessions/current", headers=headers)

    _assert_database_unavailable(response)


def test_practice_session_save_failure_rolls_back_and_returns_controlled_error(
    postgres_repository, monkeypatch
):
    headers = _headers()
    assert client.patch("/api/v1/profile", headers=headers, json=PROFILE).status_code == 200
    assert client.post("/api/v1/profile/confirm", headers=headers).status_code == 200
    selection = client.put(
        "/api/v1/practice-role",
        headers=headers,
        json={"role_id": "software_engineer", "source": "previous"},
    )
    assert selection.status_code == 200

    connection = FakeConnection(
        psycopg2.OperationalError("server closed the connection unexpectedly"),
        fails_on=lambda sql: "INSERT" in sql,
    )
    pool = FakePool(connection)
    module = postgres_repository("postgres_practice_session_repository", pool)
    monkeypatch.setattr(
        dependencies, "_practice_session_repository", module.PostgresPracticeSessionRepository()
    )

    response = client.post("/api/v1/practice-sessions", headers=headers, json=SETTINGS)

    _assert_database_unavailable(response)
    assert "closed the connection" not in response.text
    assert connection.rolled_back
    assert not connection.committed
    assert connection in pool.returned


def test_catalogue_read_failure_rolls_back_and_returns_controlled_error(
    postgres_repository, monkeypatch
):
    connection = FakeConnection(psycopg2.OperationalError(LEAKY_DETAIL))
    pool = FakePool(connection)
    module = postgres_repository("postgres_catalogue_repository", pool)
    monkeypatch.setattr(dependencies, "_catalogue_repository", module.PostgresCatalogueRepository())

    response = client.get("/api/v1/catalogue/roles")

    _assert_database_unavailable(response)
    assert connection.rolled_back
    assert pool.returned == [connection]


def test_unhandled_exception_returns_generic_error_envelope(caplog):
    def _crash():
        raise RuntimeError("secret internal detail")

    app.dependency_overrides[dependencies.get_catalogue_service] = _crash
    try:
        # A real server keeps running after an unhandled error; don't
        # re-raise it into the test the way TestClient does by default.
        with caplog.at_level(logging.ERROR):
            response = TestClient(app, raise_server_exceptions=False).get("/api/v1/catalogue/roles")
    finally:
        app.dependency_overrides.pop(dependencies.get_catalogue_service, None)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong. Please try again.",
            "details": [],
        }
    }
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" in caplog.text
