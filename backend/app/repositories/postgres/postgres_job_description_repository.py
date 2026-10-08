import json

import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.job_description_repository import (
    ExtractedSkill,
    JobDescription,
    JobDescriptionRepository,
)
from app.repositories.postgres.db_errors import database_unavailable

# One shared pool of database connections. FastAPI runs sync routes in a
# thread pool, so this must be the threaded pool variant - see
# postgres_practice_session_repository.py for the concurrent-request bug
# SimpleConnectionPool caused here before it was switched.
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

_SELECT_COLUMNS = (
    "job_description_id, owner_token_hash, raw_text, extracted_skills, "
    "extracted_responsibilities, min_years_experience, keywords, role_title_guess, created_at, "
    "closest_role_id"
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


def _execute(sql: str, params: tuple = ()) -> int:
    """Runs one write statement, commits it, and returns the affected row
    count (callers that don't need it, like add(), just ignore it)."""
    try:
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rowcount = cur.rowcount
            conn.commit()
            return rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


def _row_to_job_description(row: tuple) -> JobDescription:
    (
        job_description_id, owner_token_hash, raw_text, extracted_skills,
        extracted_responsibilities, min_years_experience, keywords, role_title_guess, created_at,
        closest_role_id,
    ) = row
    return JobDescription(
        job_description_id=job_description_id,
        owner_token_hash=owner_token_hash,
        raw_text=raw_text,
        extracted_skills=[ExtractedSkill(label=s["label"], category=s["category"]) for s in extracted_skills],
        extracted_responsibilities=list(extracted_responsibilities),
        min_years_experience=min_years_experience,
        keywords=list(keywords),
        role_title_guess=role_title_guess,
        created_at=created_at,
        closest_role_id=closest_role_id,
    )


class PostgresJobDescriptionRepository(JobDescriptionRepository):
    """Job descriptions stored in job_description, keyed by the owner's
    already-hashed session token. Each paste is its own row - add() always
    inserts, never updates (unlike profile/practice_session, there is no
    "the same one, changed" concept here)."""

    def add(self, job_description: JobDescription) -> JobDescription:
        _execute(
            """
            INSERT INTO job_description (
                job_description_id, owner_token_hash, raw_text, extracted_skills,
                extracted_responsibilities, min_years_experience, keywords, role_title_guess, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_description.job_description_id,
                job_description.owner_token_hash,
                job_description.raw_text,
                json.dumps(
                    [{"label": s.label, "category": s.category} for s in job_description.extracted_skills]
                ),
                job_description.extracted_responsibilities,
                job_description.min_years_experience,
                job_description.keywords,
                job_description.role_title_guess,
                job_description.created_at,
            ),
        )
        return job_description

    def get_for_owner(self, owner_token_hash: str, job_description_id: str) -> JobDescription | None:
        rows = _query(
            f"SELECT {_SELECT_COLUMNS} FROM job_description WHERE job_description_id = %s AND owner_token_hash = %s",
            (job_description_id, owner_token_hash),
        )
        return _row_to_job_description(rows[0]) if rows else None

    def list_for_owner(self, owner_token_hash: str) -> list[JobDescription]:
        rows = _query(
            f"SELECT {_SELECT_COLUMNS} FROM job_description WHERE owner_token_hash = %s ORDER BY created_at DESC",
            (owner_token_hash,),
        )
        return [_row_to_job_description(row) for row in rows]

    def set_closest_role(self, owner_token_hash: str, job_description_id: str, role_id: str) -> bool:
        rowcount = _execute(
            "UPDATE job_description SET closest_role_id = %s "
            "WHERE job_description_id = %s AND owner_token_hash = %s",
            (role_id, job_description_id, owner_token_hash),
        )
        return rowcount > 0

    def delete_for_owner(self, owner_token_hash: str, job_description_id: str) -> bool:
        rowcount = _execute(
            "DELETE FROM job_description WHERE job_description_id = %s AND owner_token_hash = %s",
            (job_description_id, owner_token_hash),
        )
        return rowcount > 0
