import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.vacancy_repository import (
    NATIONAL_STATE,
    RoleMarketData,
    VacancyRepository,
)
from app.repositories.postgres.db_errors import database_unavailable

# Read-only reference data (data/pipeline/build_vacancy_seed.py owns
# writing it) - still its own pool, matching every other repository in this
# backend, so a slow/broken vacancy query can't starve connections meant
# for session/profile/practice-session work.
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
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
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


class PostgresVacancyRepository(VacancyRepository):
    """Reads from role_vacancy_latest (DB 3.1's view over role_anzsco_map +
    vacancy_monthly) - see data/schema/vacancy_schema.sql."""

    def get_for_role(self, role_id: str, state: str = NATIONAL_STATE) -> RoleMarketData | None:
        rows = _query(
            """
            SELECT anzsco_code, anzsco_title, confidence, state, latest_month,
                   ads_latest, ads_12m_avg, yoy_change_pct
            FROM role_vacancy_latest
            WHERE role_id = %s AND state = %s
            """,
            (role_id, state),
        )
        if not rows:
            return None
        anzsco_code, anzsco_title, confidence, state, latest_month, ads_latest, ads_12m_avg, yoy_change_pct = rows[0]
        return RoleMarketData(
            anzsco_code=anzsco_code,
            anzsco_title=anzsco_title,
            confidence=confidence,
            state=state,
            latest_month=latest_month,
            ads_latest=ads_latest,
            ads_12m_avg=ads_12m_avg,
            yoy_change_pct=float(yoy_change_pct) if yoy_change_pct is not None else None,
        )
