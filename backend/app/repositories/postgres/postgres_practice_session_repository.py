import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.practice_session_repository import (
    PracticeRoleRef,
    PracticeScenario,
    PracticeSession,
    PracticeSessionRepository,
    ReflectiveFeedback,
    ScenarioAttempt,
    ScenarioOption,
    SuggestedSkill,
)
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

_SELECT_SESSION_SQL = """
    SELECT session_id, owner_token_hash, role_id, role_label, role_source,
           duration, difficulty, status, created_at, updated_at, completed_at
    FROM practice_session WHERE session_id = %s AND owner_token_hash = %s
"""

_SELECT_SCENARIOS_SQL = """
    SELECT scenario_id, title, workplace_area, situation, task, activity_type,
           guidance, skills_used, new_skill_focus, status,
           response_selected_option_id, response_text, response_submitted_at,
           feedback_what_worked_well, feedback_areas_to_consider, feedback_trade_offs,
           feedback_skill_to_explore_title, feedback_skill_to_explore_why, feedback_status
    FROM practice_scenario WHERE session_id = %s ORDER BY scenario_id
"""

_UPSERT_SESSION_SQL = """
    INSERT INTO practice_session (
        session_id, owner_token_hash, role_id, role_label, role_source,
        duration, difficulty, status, created_at, updated_at, completed_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (session_id) DO UPDATE SET
        status = EXCLUDED.status,
        updated_at = EXCLUDED.updated_at,
        completed_at = EXCLUDED.completed_at
"""

_UPSERT_SCENARIO_SQL = """
    INSERT INTO practice_scenario (
        scenario_id, session_id, title, workplace_area, situation, task, activity_type,
        guidance, skills_used, new_skill_focus, status,
        response_selected_option_id, response_text, response_submitted_at,
        feedback_what_worked_well, feedback_areas_to_consider, feedback_trade_offs,
        feedback_skill_to_explore_title, feedback_skill_to_explore_why, feedback_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (scenario_id) DO UPDATE SET
        status = EXCLUDED.status,
        response_selected_option_id = EXCLUDED.response_selected_option_id,
        response_text = EXCLUDED.response_text,
        response_submitted_at = EXCLUDED.response_submitted_at,
        feedback_what_worked_well = EXCLUDED.feedback_what_worked_well,
        feedback_areas_to_consider = EXCLUDED.feedback_areas_to_consider,
        feedback_trade_offs = EXCLUDED.feedback_trade_offs,
        feedback_skill_to_explore_title = EXCLUDED.feedback_skill_to_explore_title,
        feedback_skill_to_explore_why = EXCLUDED.feedback_skill_to_explore_why,
        feedback_status = EXCLUDED.feedback_status
"""


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
    a session and its scenarios either all land or none do."""
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


def _upsert_session(cur, session: PracticeSession) -> None:
    cur.execute(
        _UPSERT_SESSION_SQL,
        (
            session.session_id,
            session.owner_token_hash,
            session.role.id,
            session.role.label,
            session.role.source,
            session.duration,
            session.difficulty,
            session.status,
            session.created_at,
            session.updated_at,
            session.completed_at,
        ),
    )


def _upsert_scenario(cur, session_id: str, scenario: PracticeScenario) -> None:
    response = scenario.response
    feedback = scenario.feedback
    skill = feedback.skill_to_explore if feedback else None
    cur.execute(
        _UPSERT_SCENARIO_SQL,
        (
            scenario.scenario_id,
            session_id,
            scenario.title,
            scenario.workplace_area,
            scenario.situation,
            scenario.task,
            scenario.activity_type,
            scenario.guidance,
            scenario.skills_used,
            scenario.new_skill_focus,
            scenario.status,
            response.selected_option_id if response else None,
            response.response_text if response else None,
            response.submitted_at if response else None,
            feedback.what_worked_well if feedback else None,
            feedback.areas_to_consider if feedback else None,
            feedback.trade_offs if feedback else [],
            skill.skill if skill else None,
            skill.why_relevant if skill else None,
            scenario.feedback_status,
        ),
    )


def _insert_options(cur, scenario: PracticeScenario) -> None:
    # Options are set once when a scenario is created and never change, so a
    # later save() re-inserting the same rows is a harmless no-op.
    if not scenario.options:
        return
    execute_values(
        cur,
        """
        INSERT INTO practice_scenario_option (scenario_id, option_id, text)
        VALUES %s
        ON CONFLICT (scenario_id, option_id) DO NOTHING
        """,
        [(scenario.scenario_id, option.option_id, option.text) for option in scenario.options],
    )


def _row_to_scenario(row: tuple, options: list[ScenarioOption]) -> PracticeScenario:
    (
        scenario_id, title, workplace_area, situation, task, activity_type,
        guidance, skills_used, new_skill_focus, status,
        resp_option_id, resp_text, resp_submitted_at,
        fb_worked_well, fb_areas, fb_trade_offs, fb_skill_title, fb_skill_why, fb_status,
    ) = row

    response = None
    if resp_submitted_at is not None:
        response = ScenarioAttempt(
            submitted_at=resp_submitted_at,
            response_text=resp_text,
            selected_option_id=resp_option_id,
        )

    feedback = None
    if fb_status == "available":
        feedback = ReflectiveFeedback(
            what_worked_well=list(fb_worked_well or []),
            areas_to_consider=list(fb_areas or []),
            trade_offs=list(fb_trade_offs or []),
            skill_to_explore=SuggestedSkill(skill=fb_skill_title, why_relevant=fb_skill_why)
            if fb_skill_title is not None
            else None,
        )

    return PracticeScenario(
        scenario_id=scenario_id,
        title=title,
        workplace_area=workplace_area,
        situation=situation,
        task=task,
        activity_type=activity_type,
        guidance=list(guidance),
        skills_used=list(skills_used),
        new_skill_focus=new_skill_focus,
        options=options,
        status=status,
        response=response,
        feedback=feedback,
        feedback_status=fb_status,
    )


def _row_to_session(row: tuple, scenarios: list[PracticeScenario]) -> PracticeSession:
    (
        session_id, owner_token_hash, role_id, role_label, role_source,
        duration, difficulty, status, created_at, updated_at, completed_at,
    ) = row
    return PracticeSession(
        session_id=session_id,
        owner_token_hash=owner_token_hash,
        role=PracticeRoleRef(id=role_id, label=role_label, source=role_source),
        duration=duration,
        difficulty=difficulty,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        scenarios=scenarios,
        completed_at=completed_at,
    )


def _load_scenarios(session_id: str) -> list[PracticeScenario]:
    scenarios = []
    for row in _query(_SELECT_SCENARIOS_SQL, (session_id,)):
        option_rows = _query(
            "SELECT option_id, text FROM practice_scenario_option WHERE scenario_id = %s ORDER BY option_id",
            (row[0],),
        )
        options = [ScenarioOption(option_id=option_id, text=text) for option_id, text in option_rows]
        scenarios.append(_row_to_scenario(row, options))
    return scenarios


class PostgresPracticeSessionRepository(PracticeSessionRepository):
    """Practice sessions stored in practice_session/practice_scenario/
    practice_scenario_option, keyed by the owner's already-hashed session
    token. A session's scenarios are upserted alongside it on both add()
    and save(), since ScenarioResponseService mutates a scenario's response
    and feedback fields in place and then calls save() with the whole
    session."""

    def _persist(self, session: PracticeSession) -> PracticeSession:
        def _do(cur):
            _upsert_session(cur, session)
            for scenario in session.scenarios:
                _upsert_scenario(cur, session.session_id, scenario)
                _insert_options(cur, scenario)

        _run_in_transaction(_do)
        return session

    def add(self, session: PracticeSession) -> PracticeSession:
        return self._persist(session)

    def get_for_owner(self, owner_token_hash: str, session_id: str) -> PracticeSession | None:
        rows = _query(_SELECT_SESSION_SQL, (session_id, owner_token_hash))
        if not rows:
            return None
        return _row_to_session(rows[0], _load_scenarios(session_id))

    def get_active_for_owner(self, owner_token_hash: str) -> PracticeSession | None:
        rows = _query(
            """
            SELECT session_id FROM practice_session
            WHERE owner_token_hash = %s AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
            """,
            (owner_token_hash,),
        )
        if not rows:
            return None
        return self.get_for_owner(owner_token_hash, rows[0][0])

    def save(self, session: PracticeSession) -> PracticeSession:
        return self._persist(session)
