from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnonSession:
    """One anonymous journey. This is plain internal data - not the API
    shape (that is a schema) and not a database row (that is the database
    team's job).

    Only the SHA-256 hash of the access token is kept, matching
    anon_session.token_hash in the database schema. The raw token is returned
    to the user once, when the session is created, and never stored."""
    token_hash: str
    created_at: datetime
    last_seen_at: datetime


class SessionRepository(ABC):
    """Storage contract any session store must follow, whether it keeps
    data in memory (now) or in a real database (later). Services depend on
    this interface, never on a specific store."""

    @abstractmethod
    def add(self, session: AnonSession) -> AnonSession:
        """Save a new session and return it. Used right after a session
        is created."""
        raise NotImplementedError

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> AnonSession | None:
        """Return the session with this token hash, or None if none exists.
        Used to check a session is still valid on every protected request."""
        raise NotImplementedError

    @abstractmethod
    def touch(self, token_hash: str, seen_at: datetime) -> None:
        """Record that the session was used. Does nothing for an unknown
        hash."""
        raise NotImplementedError

    def get_and_touch(self, token_hash: str, seen_at: datetime) -> AnonSession | None:
        """Return the session with this token hash and record that it was
        used, or None if none exists. A store may override this to do both
        in one step."""
        session = self.get_by_token_hash(token_hash)
        if session is None:
            return None
        self.touch(token_hash, seen_at)
        session.last_seen_at = seen_at
        return session

    @abstractmethod
    def delete(self, token_hash: str) -> bool:
        """Delete this session (AC 3.5.2, Clear My Journey). The token
        stops working immediately after - every later request with it
        fails get_current_session's lookup. Return True if a session
        existed and was deleted."""
        raise NotImplementedError
