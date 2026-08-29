
from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


class MemorySessionRepository(SessionRepository):
    """DEVELOPMENT-ONLY session store. Data lives in a dict and is LOST on
    restart. Swapped for a PostgreSQL implementation after the DB handover."""

    def __init__(self) -> None:
        self._sessions: dict[str, AnonSession] = {}  # token -> session

    def add(self, session: AnonSession) -> AnonSession:
        self._sessions[session.token] = session      # store it
        return session

    def get_by_token(self, token: str) -> AnonSession | None:
        return self._sessions.get(token)             # None if not found