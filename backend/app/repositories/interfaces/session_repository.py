from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnonSession:
    """One anonymous journey. This is the backend's INTERNAL representation —
    not the API shape (that'll be a schema) and not a database row
    (that's the DB teammate's job). Just plain data we pass around."""
    token: str
    created_at: datetime
    last_seen_at: datetime


class SessionRepository(ABC):
    """The CONTRACT any session store must fulfil — whether it stores data
    in memory (now) or in PostgreSQL (later). Services depend on this
    abstract class, never on a concrete store."""

    @abstractmethod
    def add(self, session: AnonSession) -> AnonSession:
        """Save a new session and return it."""
        raise NotImplementedError

    @abstractmethod
    def get_by_token(self, token: str) -> AnonSession | None:
        """Return the session with this token, or None if none exists."""
        raise NotImplementedError