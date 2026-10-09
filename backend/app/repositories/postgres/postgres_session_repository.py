from datetime import datetime

import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.session_repository import AnonSession, SessionRepository
from app.repositories.postgres.db_errors import database_unavailable
from app.repositories.postgres.pooling import KEEPALIVE, checkout, release, rollback_quietly

# One shared pool of database connections, reused across every request
# instead of opening a new connection each time. FastAPI runs sync routes
# in a thread pool, so this must be the threaded pool variant -
# SimpleConnectionPool's own docstring says it "can't be shared across
# different threads" (see postgres_practice_session_repository.py for the
# concurrent-request bug this caused).
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode=DB_SSLMODE,
    **KEEPALIVE,
)


def _query(sql: str, params: tuple = ()) -> list[tuple]:
    try:
        conn = checkout(_pool)
        try:
            # Autocommit: a lone statement needs no BEGIN/COMMIT, and each of
            # those is a full round trip to a database that is far away.
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception:
            # A failed statement leaves the connection in an aborted
            # transaction; roll back so the pool doesn't hand it out broken.
            rollback_quietly(conn)
            raise
        finally:
            release(_pool, conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


def _execute(sql: str, params: tuple = ()) -> int:
    """Runs one write statement, commits it, and returns the affected row
    count (most callers ignore it - delete() is the one that needs it)."""
    try:
        conn = checkout(_pool)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount
        except Exception:
            rollback_quietly(conn)
            raise
        finally:
            release(_pool, conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


class PostgresSessionRepository(SessionRepository):
    """Sessions stored in anon_session, keyed by the already-hashed token
    (SessionService hashes the raw token before it ever reaches this
    class - see app/core/tokens.py). Only the hash is ever stored, matching
    the schema's comment that the raw token must never be kept."""

    def add(self, session: AnonSession) -> AnonSession:
        _execute(
            "INSERT INTO anon_session (token_hash, created_at, last_seen_at) VALUES (%s, %s, %s)",
            (session.token_hash, session.created_at, session.last_seen_at),
        )
        return session

    def get_by_token_hash(self, token_hash: str) -> AnonSession | None:
        rows = _query(
            "SELECT created_at, last_seen_at FROM anon_session WHERE token_hash = %s",
            (token_hash,),
        )
        if not rows:
            return None
        created_at, last_seen_at = rows[0]
        return AnonSession(token_hash=token_hash, created_at=created_at, last_seen_at=last_seen_at)

    def touch(self, token_hash: str, seen_at: datetime) -> None:
        _execute(
            "UPDATE anon_session SET last_seen_at = %s WHERE token_hash = %s",
            (seen_at, token_hash),
        )

    def get_and_touch(self, token_hash: str, seen_at: datetime) -> AnonSession | None:
        # Runs on every protected request, so lookup and touch share one
        # statement.
        rows = _query(
            "UPDATE anon_session SET last_seen_at = %s WHERE token_hash = %s RETURNING created_at",
            (seen_at, token_hash),
        )
        if not rows:
            return None
        return AnonSession(token_hash=token_hash, created_at=rows[0][0], last_seen_at=seen_at)

    def delete(self, token_hash: str) -> bool:
        # Cascades to profile, job_description and practice_session (and
        # its own child tables) via their ON DELETE CASCADE foreign keys -
        # one row delete clears the entire journey.
        rowcount = _execute("DELETE FROM anon_session WHERE token_hash = %s", (token_hash,))
        return rowcount > 0
