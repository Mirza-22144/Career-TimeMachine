from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ExtractedSkill:
    """One skill found in a job description. A plain dataclass, not a
    database model - the database teammate persists the same fields behind
    the repository interface."""

    label: str
    category: str  # "technical" or "soft"


@dataclass
class JobDescription:
    """One job description a user has pasted, with its extracted
    requirements. Keyed by the owner's already-hashed session token - a
    token can have several of these over time (Step 12's dashboard needs
    all of them, not just the latest)."""

    job_description_id: str
    owner_token_hash: str
    raw_text: str
    extracted_skills: list[ExtractedSkill] = field(default_factory=list)
    extracted_responsibilities: list[str] = field(default_factory=list)
    min_years_experience: int | None = None
    keywords: list[str] = field(default_factory=list)
    role_title_guess: str | None = None
    created_at: datetime | None = None


class JobDescriptionRepository(ABC):
    """Stores job descriptions and their extracted requirements."""

    @abstractmethod
    def add(self, job_description: JobDescription) -> JobDescription:
        """Store a new job description. Never updates an existing one -
        each paste is its own record."""
        raise NotImplementedError

    @abstractmethod
    def get_for_owner(self, owner_token_hash: str, job_description_id: str) -> JobDescription | None:
        """Return one of the owner's job descriptions. Another owner's
        record must never be returned, even with the right id."""
        raise NotImplementedError

    @abstractmethod
    def list_for_owner(self, owner_token_hash: str) -> list[JobDescription]:
        """Return all of the owner's job descriptions, newest first."""
        raise NotImplementedError

    @abstractmethod
    def delete_for_owner(self, owner_token_hash: str, job_description_id: str) -> bool:
        """Delete one of the owner's job descriptions (AC 3.5.1). Return
        True if a matching record existed and was deleted - another
        owner's record, or an unknown id, must never be deleted or even
        reveal whether it exists."""
        raise NotImplementedError
