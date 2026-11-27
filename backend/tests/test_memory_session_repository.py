from datetime import datetime, timezone
from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.memory.memory_session_repository import MemorySessionRepository


def test_add_then_get_returns_the_session():
    repo = MemorySessionRepository()
    now = datetime.now(timezone.utc)
    s = AnonSession(token="abc123", created_at=now, last_seen_at=now)
    repo.add(s)
    assert repo.get_by_token("abc123") is s        # stored & retrieved


def test_get_unknown_token_returns_none():
    assert MemorySessionRepository().get_by_token("nope") is None

    