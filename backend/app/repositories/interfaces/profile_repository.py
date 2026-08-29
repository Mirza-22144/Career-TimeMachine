from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Profile:
    """Internal profile data for one anonymous session.

    This is a plain dataclass on purpose: it is not a Pydantic schema and not
    a database model. The database teammate can later persist the same fields
    behind the repository interface.
    """

    # The anonymous session owns the profile; routes never expose profile ids.
    session_token: str

    # Previous career details captured from catalogue selections or free text.
    role_id: str | None = None
    role_other_text: str | None = None
    years_experience: str | None = None

    # Skill and responsibility IDs come from the catalogue; custom values are
    # cleaned user-entered labels for options the catalogue does not include.
    skill_ids: list[str] = field(default_factory=list)
    custom_skills: list[str] = field(default_factory=list)
    responsibility_ids: list[str] = field(default_factory=list)
    custom_responsibilities: list[str] = field(default_factory=list)

    # The break reason is stored and echoed only. Do not use it in readiness,
    # strengths, or other business logic.
    break_reason: str | None = None
    break_reason_other_text: str | None = None

    # Return timing. If return_date_unsure is true, planned_return_date is
    # forced to None by the service.
    break_started_on: date | None = None
    planned_return_date: date | None = None
    return_date_unsure: bool = False

    # Computed by the service whenever dates change.
    break_duration_months: int | None = None

    # Confirmation means the profile passed the completeness rules. Later edits
    # invalidate this flag so the frontend can ask the user to reconfirm.
    confirmed: bool = False


class ProfileRepository(ABC):
    """Storage contract for profiles.

    Services depend on this interface, so the in-memory store can be replaced
    by PostgreSQL later without changing routes or business logic.
    """

    @abstractmethod
    def get_by_session_token(self, session_token: str) -> Profile | None:
        """Return the profile for a session, or None if it does not exist."""
        raise NotImplementedError

    @abstractmethod
    def save(self, profile: Profile) -> Profile:
        """Create or replace the profile for its session token."""
        raise NotImplementedError

    @abstractmethod
    def delete_by_session_token(self, session_token: str) -> bool:
        """Delete the profile for a session; return True if one existed."""
        raise NotImplementedError
