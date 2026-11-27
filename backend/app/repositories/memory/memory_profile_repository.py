from app.repositories.interfaces.profile_repository import Profile, ProfileRepository


class MemoryProfileRepository(ProfileRepository):
    """DEVELOPMENT-ONLY profile store.

    Data lives in memory and is lost when the app restarts. This class exists
    only so the backend can be exercised before the database handover.
    """

    def __init__(self) -> None:
        # Key profiles by anonymous session token: one profile per session.
        self._profiles: dict[str, Profile] = {}

    def get_by_session_token(self, session_token: str) -> Profile | None:
        """Look up a profile without creating one."""
        return self._profiles.get(session_token)

    def save(self, profile: Profile) -> Profile:
        """Store the latest profile state for the owning session."""
        self._profiles[profile.session_token] = profile
        return profile

    def delete_by_session_token(self, session_token: str) -> bool:
        """Remove a session's profile and report whether anything changed."""
        return self._profiles.pop(session_token, None) is not None
