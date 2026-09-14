from datetime import datetime

from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


class MemorySessionRepository(SessionRepository):
    """Session store backed by a plain dict. Data is lost when the server
    restarts. Will be swapped for a real database store later."""

    def __init__(self) -> None:
        self._sessions: dict[str, AnonSession] = {}  # token hash -> session

    def add(self, session: AnonSession) -> AnonSession:
        """Save a new session under its token hash."""
        self._sessions[session.token_hash] = session
        return session

    def get_by_token_hash(self, token_hash: str) -> AnonSession | None:
        """Look up a session by its token hash, or return None if not found."""
        return self._sessions.get(token_hash)

    def touch(self, token_hash: str, seen_at: datetime) -> None:
        """Update last_seen_at for a known session."""
        session = self._sessions.get(token_hash)
        if session is not None:
            session.last_seen_at = seen_at
