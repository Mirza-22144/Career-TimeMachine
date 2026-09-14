from datetime import datetime, timedelta, timezone
from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.memory.memory_session_repository import MemorySessionRepository


def test_add_then_get_returns_the_session():
    repo = MemorySessionRepository()
    now = datetime.now(timezone.utc)
    s = AnonSession(token_hash="abc123", created_at=now, last_seen_at=now)
    repo.add(s)
    assert repo.get_by_token_hash("abc123") is s   # stored & retrieved


def test_get_unknown_token_hash_returns_none():
    assert MemorySessionRepository().get_by_token_hash("nope") is None


def test_touch_updates_last_seen_at_only_for_known_sessions():
    repo = MemorySessionRepository()
    now = datetime.now(timezone.utc)
    later = now + timedelta(minutes=5)
    repo.add(AnonSession(token_hash="abc123", created_at=now, last_seen_at=now))

    repo.touch("abc123", later)
    repo.touch("nope", later)                      # unknown hash is ignored

    assert repo.get_by_token_hash("abc123").last_seen_at == later
    assert repo.get_by_token_hash("nope") is None
