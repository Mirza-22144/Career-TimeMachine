import secrets
from datetime import datetime, timezone

from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


class SessionService:
    """Creates and looks up anonymous sessions. Used by the anonymous-
    sessions route and by get_current_session for every protected route."""

    # Depends on the interface, never a concrete store, so storage can change.
    def __init__(self, sessions: SessionRepository) -> None:
        self.sessions = sessions

    def start_session(self) -> AnonSession:
        """Create and save a new anonymous session with a random token."""
        now = datetime.now(timezone.utc)
        session = AnonSession(
            token=secrets.token_urlsafe(32),  # random, unguessable (not sequential)
            created_at=now,
            last_seen_at=now,
        )
        return self.sessions.add(session)

    def get_current(self, token: str) -> AnonSession | None:
        """Look up a session by its token, or return None if not found."""
        return self.sessions.get_by_token(token)

    