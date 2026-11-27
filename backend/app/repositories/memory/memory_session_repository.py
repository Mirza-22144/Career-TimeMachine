from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


class MemorySessionRepository(SessionRepository):
    """Session store backed by a plain dict. Data is lost when the server
    restarts. Will be swapped for a real database store later."""

    def __init__(self) -> None:
        self._sessions: dict[str, AnonSession] = {}  # token -> session

    def add(self, session: AnonSession) -> AnonSession:
        """Save a new session under its token."""
        self._sessions[session.token] = session
        return session

    def get_by_token(self, token: str) -> AnonSession | None:
        """Look up a session by its token, or return None if not found."""
        return self._sessions.get(token)
