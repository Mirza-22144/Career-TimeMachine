from copy import deepcopy

from app.repositories.interfaces.practice_session_repository import (
    PracticeSession,
    PracticeSessionRepository,
)


class MemoryPracticeSessionRepository(PracticeSessionRepository):
    """DEVELOPMENT-ONLY practice session store.

    Data is lost when the app restarts. Sessions are copied in and out, like
    database rows, so changes only take effect through add() or save().
    """

    def __init__(self) -> None:
        self._sessions: dict[str, PracticeSession] = {}  # session_id -> session

    def add(self, session: PracticeSession) -> PracticeSession:
        self._sessions[session.session_id] = deepcopy(session)
        return deepcopy(session)

    def get_for_owner(self, owner_token_hash: str, session_id: str) -> PracticeSession | None:
        session = self._sessions.get(session_id)
        if session is None or session.owner_token_hash != owner_token_hash:
            return None
        return deepcopy(session)

    def get_active_for_owner(self, owner_token_hash: str) -> PracticeSession | None:
        active = [
            session
            for session in self._sessions.values()
            if session.owner_token_hash == owner_token_hash and session.status == "active"
        ]
        if not active:
            return None
        return deepcopy(max(active, key=lambda session: session.created_at))

    def save(self, session: PracticeSession) -> PracticeSession:
        self._sessions[session.session_id] = deepcopy(session)
        return deepcopy(session)
