from datetime import datetime

import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.session_repository import AnonSession, SessionRepository
from app.repositories.postgres.db_errors import database_unavailable

# One shared pool of database connections, reused across every request
# instead of opening a new connection each time.
_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode=DB_SSLMODE,
)


def _query(sql: str, params: tuple = ()) -> list[tuple]:
    try:
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception:
            # A failed statement leaves the connection in an aborted
            # transaction; roll back so the pool doesn't hand it out broken.
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


def _execute(sql: str, params: tuple = ()) -> None:
    """Runs one write statement and commits it."""
    try:
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
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
