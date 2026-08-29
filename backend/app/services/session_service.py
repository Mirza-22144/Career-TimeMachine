import secrets
from datetime import datetime, timezone

from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


class SessionService:
    # Depends on the INTERFACE, never a concrete store -> storage is swappable.
    def __init__(self, sessions: SessionRepository) -> None:
        self.sessions = sessions

    def start_session(self) -> AnonSession:
        now = datetime.now(timezone.utc)
        session = AnonSession(
            token=secrets.token_urlsafe(32),  # random, unguessable (not sequential)
            created_at=now,
            last_seen_at=now,
        )
        return self.sessions.add(session)

    def get_current(self, token: str) -> AnonSession | None:
        return self.sessions.get_by_token(token)

    