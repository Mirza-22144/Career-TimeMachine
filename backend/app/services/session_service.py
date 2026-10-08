from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.tokens import generate_token, hash_token, is_well_formed_token
from app.repositories.interfaces.job_description_repository import JobDescriptionRepository
from app.repositories.interfaces.profile_repository import ProfileRepository
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

    # Depends on interfaces, never concrete stores, so storage can change.
    # profiles/job_descriptions are optional: only clear_journey (AC 3.5.2)
    # needs them, and every other existing call site shouldn't be forced to
    # supply dependencies it never uses.
    def __init__(
        self,
        sessions: SessionRepository,
        profiles: ProfileRepository | None = None,
        job_descriptions: JobDescriptionRepository | None = None,
    ) -> None:
        self.sessions = sessions
        self.profiles = profiles
        self.job_descriptions = job_descriptions

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

    def clear_journey(self, token_hash: str) -> None:
        """AC 3.5.2: permanently delete everything tied to this token - the
        profile, every saved job description, and the session itself. The
        token stops working immediately after. Postgres cascades this
        automatically from anon_session's foreign keys when the session
        row is deleted; the explicit profile/job-description deletes here
        make the in-memory store (no real foreign keys) behave the same
        way, so this is correct under either backing store."""
        if self.profiles is not None:
            self.profiles.delete_by_session_token(token_hash)
        if self.job_descriptions is not None:
            for job_description in self.job_descriptions.list_for_owner(token_hash):
                self.job_descriptions.delete_for_owner(token_hash, job_description.job_description_id)
        self.sessions.delete(token_hash)
