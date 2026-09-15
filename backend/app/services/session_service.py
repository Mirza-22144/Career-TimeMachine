from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.tokens import generate_token, hash_token, is_well_formed_token
from app.repositories.interfaces.session_repository import (
    AnonSession,
    SessionRepository,
)


@dataclass
class IssuedSession:
    """A newly created session together with its raw access token. This is
    the only object that carries the raw token, and only so the create
    endpoint can return it once."""

    token: str
    created_at: datetime
    last_seen_at: datetime


class SessionService:
    """Creates and looks up anonymous sessions. Used by the anonymous-
    sessions route and by get_current_session for every protected route."""

    # Depends on the interface, never a concrete store, so storage can change.
    def __init__(self, sessions: SessionRepository) -> None:
        self.sessions = sessions

    def start_session(self) -> IssuedSession:
        """Create a session with a random token; store only the token hash."""
        now = datetime.now(timezone.utc)
        token = generate_token()  # random, unguessable (not sequential)
        self.sessions.add(
            AnonSession(token_hash=hash_token(token), created_at=now, last_seen_at=now)
        )
        return IssuedSession(token=token, created_at=now, last_seen_at=now)

    def get_current(self, token: str) -> AnonSession | None:
        """Return the session for a raw token and record the visit, or None
        if the token is malformed or unknown."""
        if not is_well_formed_token(token):
            return None

        token_hash = hash_token(token)
        session = self.sessions.get_by_token_hash(token_hash)
        if session is None:
            return None

        now = datetime.now(timezone.utc)
        self.sessions.touch(token_hash, now)
        session.last_seen_at = now
        return session
