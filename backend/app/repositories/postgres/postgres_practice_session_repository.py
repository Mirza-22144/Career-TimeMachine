import json

import psycopg2
import psycopg2.pool

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
# instead of opening a new connection each time. FastAPI runs these sync
# routes in a thread pool, so this must be the threaded pool variant -
# SimpleConnectionPool's own docstring says it "can't be shared across
# different threads"; using it here silently corrupted concurrent requests
# (a write from one thread going missing with no raised error) until this
# was caught and fixed.
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

_SELECT_SESSION_SQL = """
    SELECT session_id, owner_token_hash, role_id, role_label, role_source,
           duration, difficulty, status, created_at, updated_at, completed_at
    FROM practice_session WHERE session_id = %s AND owner_token_hash = %s
"""

_SELECT_OWNER_SESSIONS_SQL = """
    SELECT session_id, owner_token_hash, role_id, role_label, role_source,
           duration, difficulty, status, created_at, updated_at, completed_at
    FROM practice_session WHERE owner_token_hash = %s ORDER BY created_at
"""

_SELECT_ACTIVE_SESSION_SQL = """
    SELECT session_id, owner_token_hash, role_id, role_label, role_source,
           duration, difficulty, status, created_at, updated_at, completed_at
    FROM practice_session WHERE owner_token_hash = %s AND status = 'active'
    ORDER BY created_at DESC LIMIT 1
"""

_SELECT_SCENARIOS_SQL = """
    SELECT session_id, scenario_id, title, workplace_area, situation, task, activity_type,
           guidance, skills_used, new_skill_focus, status,
           response_selected_option_id, response_text, response_submitted_at,
           feedback_what_worked_well, feedback_areas_to_consider, feedback_trade_offs,
           feedback_skill_to_explore_title, feedback_skill_to_explore_why, feedback_status,
           option_feedback
    FROM practice_scenario WHERE session_id = ANY(%s) ORDER BY scenario_id
"""

_SELECT_OPTIONS_SQL = """
    SELECT session_id, scenario_id, option_id, text
    FROM practice_scenario_option WHERE session_id = ANY(%s) ORDER BY option_id
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
        feedback_skill_to_explore_title, feedback_skill_to_explore_why, feedback_status,
        option_feedback
    ) VALUES %s
    ON CONFLICT (session_id, scenario_id) DO UPDATE SET
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
            # Autocommit: a lone statement needs no BEGIN/COMMIT, and each of
            # those is a full round trip to a database that is far away.
            conn.autocommit = True
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


def _execute_together(build) -> None:
    """Runs every statement build(cursor) returns in a single round trip.
    Postgres treats statements sent together as one transaction, so a
    session and its scenarios still either all land or none do."""
    try:
        conn = _pool.getconn()
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(b";".join(build(cur)))
        except Exception:
            conn.rollback()
            raise
        finally:
            _pool.putconn(conn)
    except psycopg2.Error as exc:
        raise database_unavailable(exc) from exc


def _values_statement(cur, sql: str, rows: list[tuple]) -> bytes:
    """Fill a "VALUES %s" statement with every row, safely quoted."""
    template = "(" + ",".join(["%s"] * len(rows[0])) + ")"
    head, tail = sql.split("%s")
    return head.encode() + b",".join(cur.mogrify(template, row) for row in rows) + tail.encode()


def _session_statement(cur, session: PracticeSession) -> bytes:
    return cur.mogrify(
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


def _scenario_row(session_id: str, scenario: PracticeScenario) -> tuple:
    response = scenario.response
    feedback = scenario.feedback
    skill = feedback.skill_to_explore if feedback else None
    return (
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
        json.dumps(scenario.option_feedback) if scenario.option_feedback is not None else None,
    )


_INSERT_OPTIONS_SQL = """
    INSERT INTO practice_scenario_option (session_id, scenario_id, option_id, text)
    VALUES %s
    ON CONFLICT (session_id, scenario_id, option_id) DO NOTHING
"""


def _scenario_statements(cur, session_id: str, scenarios: list[PracticeScenario]) -> list[bytes]:
    if not scenarios:
        return []
    statements = [
        _values_statement(cur, _UPSERT_SCENARIO_SQL, [_scenario_row(session_id, scenario) for scenario in scenarios])
    ]
    # Options are set once when a scenario is created and never change, so a
    # later save() re-inserting the same rows is a harmless no-op. Keyed by
    # (session_id, scenario_id, option_id) - see fix_practice_scenario_
    # session_scoping.sql for why scenario_id alone is not unique.
    options = [
        (session_id, scenario.scenario_id, option.option_id, option.text)
        for scenario in scenarios
        for option in scenario.options
    ]
    if options:
        statements.append(_values_statement(cur, _INSERT_OPTIONS_SQL, options))
    return statements


def _row_to_scenario(row: tuple, options: list[ScenarioOption]) -> PracticeScenario:
    (
        _session_id, scenario_id, title, workplace_area, situation, task, activity_type,
        guidance, skills_used, new_skill_focus, status,
        resp_option_id, resp_text, resp_submitted_at,
        fb_worked_well, fb_areas, fb_trade_offs, fb_skill_title, fb_skill_why, fb_status,
        option_feedback,
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
        option_feedback=option_feedback,
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


def _load_sessions(session_rows: list[tuple]) -> list[PracticeSession]:
    """Attach scenarios and options to the given session rows in two queries
    in total, however many sessions there are."""
    if not session_rows:
        return []
    session_ids = [row[0] for row in session_rows]

    options: dict[tuple[str, str], list[ScenarioOption]] = {}
    for session_id, scenario_id, option_id, text in _query(_SELECT_OPTIONS_SQL, (session_ids,)):
        options.setdefault((session_id, scenario_id), []).append(ScenarioOption(option_id=option_id, text=text))

    scenarios: dict[str, list[PracticeScenario]] = {}
    for row in _query(_SELECT_SCENARIOS_SQL, (session_ids,)):
        scenarios.setdefault(row[0], []).append(_row_to_scenario(row, options.get((row[0], row[1]), [])))

    return [_row_to_session(row, scenarios.get(row[0], [])) for row in session_rows]


class PostgresPracticeSessionRepository(PracticeSessionRepository):
    """Practice sessions stored in practice_session/practice_scenario/
    practice_scenario_option, keyed by the owner's already-hashed session
    token. A session's scenarios are upserted alongside it on both add()
    and save(), since ScenarioResponseService mutates a scenario's response
    and feedback fields in place and then calls save() with the whole
    session."""

    def _persist(self, session: PracticeSession) -> PracticeSession:
        _execute_together(
            lambda cur: [
                _session_statement(cur, session),
                *_scenario_statements(cur, session.session_id, session.scenarios),
            ]
        )
        return session

    def add(self, session: PracticeSession) -> PracticeSession:
        return self._persist(session)

    def get_for_owner(self, owner_token_hash: str, session_id: str) -> PracticeSession | None:
        rows = _query(_SELECT_SESSION_SQL, (session_id, owner_token_hash))
        sessions = _load_sessions(rows[:1])
        return sessions[0] if sessions else None

    def get_active_for_owner(self, owner_token_hash: str) -> PracticeSession | None:
        sessions = _load_sessions(_query(_SELECT_ACTIVE_SESSION_SQL, (owner_token_hash,)))
        return sessions[0] if sessions else None

    def save(self, session: PracticeSession) -> PracticeSession:
        return self._persist(session)

    def list_for_owner(self, owner_token_hash: str) -> list[PracticeSession]:
        return _load_sessions(_query(_SELECT_OWNER_SESSIONS_SQL, (owner_token_hash,)))

    def add_scenario(self, owner_token_hash: str, session_id: str, scenario: PracticeScenario) -> bool:
        open_rows = _query(
            """
            SELECT 1 FROM practice_session s
            JOIN practice_scenario c ON c.session_id = s.session_id
            WHERE s.session_id = %s AND s.owner_token_hash = %s
              AND s.status = 'active' AND c.status = 'current'
            LIMIT 1
            """,
            (session_id, owner_token_hash),
        )
        if not open_rows:
            return False
        # Only this question's own rows are written, so an answer being
        # saved at the same moment is never overwritten.
        _execute_together(lambda cur: _scenario_statements(cur, session_id, [scenario]))
        return True
