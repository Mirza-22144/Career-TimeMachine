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
