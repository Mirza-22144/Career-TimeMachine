import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
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

_PROFILE_COLUMNS = (
    "role_id", "role_other_text", "years_experience", "custom_skills",
    "custom_responsibilities", "break_reason", "break_reason_other_text",
    "break_started_on", "planned_return_date", "return_date_unsure",
    "break_duration_months", "return_readiness", "area_to_explore", "confirmed",
    "practice_role_id", "practice_role_source",
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


def _run_in_transaction(fn):
    """Runs fn(cursor) and commits only if it completes without raising, so
    the profile upsert and its junction-table delete+insert either all land
    or none do."""
    try:
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                result = fn(cur)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


class PostgresProfileRepository(ProfileRepository):
    """Profiles stored in `profile`, keyed by the session's already-hashed
    token (Profile.session_token holds the hash - see
    app/repositories/interfaces/profile_repository.py). Skill and
    responsibility selections live in the profile_skill/profile_responsibility
    junction tables, fully replaced on every save() since Profile always
    carries the complete desired list, never a partial one."""

    def get_by_session_token(self, session_token: str) -> Profile | None:
        rows = _query(
            f"SELECT {', '.join(_PROFILE_COLUMNS)} FROM profile WHERE session_token_hash = %s",
            (session_token,),
        )
        if not rows:
            return None

        values = dict(zip(_PROFILE_COLUMNS, rows[0]))
        skill_rows = _query(
            "SELECT skill_id FROM profile_skill WHERE session_token_hash = %s", (session_token,)
        )
        responsibility_rows = _query(
            "SELECT responsibility_id FROM profile_responsibility WHERE session_token_hash = %s",
            (session_token,),
        )

        return Profile(
            session_token=session_token,
            skill_ids=[r[0] for r in skill_rows],
            responsibility_ids=[r[0] for r in responsibility_rows],
            **values,
        )

    def save(self, profile: Profile) -> Profile:
        session_token = profile.session_token

        def _do(cur):
            cur.execute(
                f"""
                INSERT INTO profile (session_token_hash, {', '.join(_PROFILE_COLUMNS)})
                VALUES (%s, {', '.join(['%s'] * len(_PROFILE_COLUMNS))})
                ON CONFLICT (session_token_hash) DO UPDATE SET
                    {', '.join(f"{c} = EXCLUDED.{c}" for c in _PROFILE_COLUMNS)}
                """,
                (session_token, *(getattr(profile, c) for c in _PROFILE_COLUMNS)),
            )

            cur.execute("DELETE FROM profile_skill WHERE session_token_hash = %s", (session_token,))
            if profile.skill_ids:
                execute_values(
                    cur,
                    "INSERT INTO profile_skill (session_token_hash, skill_id) VALUES %s",
                    [(session_token, sid) for sid in profile.skill_ids],
                )

            cur.execute(
                "DELETE FROM profile_responsibility WHERE session_token_hash = %s", (session_token,)
            )
            if profile.responsibility_ids:
                execute_values(
                    cur,
                    "INSERT INTO profile_responsibility (session_token_hash, responsibility_id) VALUES %s",
                    [(session_token, rid) for rid in profile.responsibility_ids],
                )

        _run_in_transaction(_do)
        return profile

    def delete_by_session_token(self, session_token: str) -> bool:
        # profile_skill/profile_responsibility both cascade on delete from
        # profile(session_token_hash), so deleting the profile row alone
        # cleans those up too.
        def _do(cur):
            cur.execute("DELETE FROM profile WHERE session_token_hash = %s", (session_token,))
            return cur.rowcount > 0

        return _run_in_transaction(_do)
