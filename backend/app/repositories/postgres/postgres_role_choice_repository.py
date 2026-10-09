from datetime import datetime

import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.role_choice_repository import RoleChoice, RoleChoiceRepository
from app.repositories.postgres.db_errors import database_unavailable
from app.repositories.postgres.pooling import KEEPALIVE, checkout, release, rollback_quietly

# Threaded pool - FastAPI runs sync routes in a thread pool (see
# postgres_practice_session_repository.py).
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode=DB_SSLMODE,
    **KEEPALIVE,
)


def _run(sql: str, params: tuple, fetch: bool) -> list[tuple]:
    try:
        conn = checkout(_pool)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else []
            conn.commit()
            return rows
        except Exception:
            rollback_quietly(conn)
            raise
        finally:
            release(_pool, conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


class PostgresRoleChoiceRepository(RoleChoiceRepository):
    """Chosen roles stored in role_choice (data/schema/add_role_choice_table.sql)."""

    def record(self, owner_token_hash: str, role_id: str, chosen_at: datetime) -> None:
        _run(
            """
            INSERT INTO role_choice (owner_token_hash, role_id, chosen_at) VALUES (%s, %s, %s)
            ON CONFLICT (owner_token_hash, role_id) DO UPDATE SET chosen_at = EXCLUDED.chosen_at
            """,
            (owner_token_hash, role_id, chosen_at),
            fetch=False,
        )

    def list_for_owner(self, owner_token_hash: str) -> list[RoleChoice]:
        rows = _run(
            "SELECT role_id, chosen_at FROM role_choice WHERE owner_token_hash = %s ORDER BY chosen_at DESC",
            (owner_token_hash,),
            fetch=True,
        )
        return [RoleChoice(role_id=role_id, chosen_at=chosen_at) for role_id, chosen_at in rows]
