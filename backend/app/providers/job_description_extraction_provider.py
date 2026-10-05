"""Boundary between the backend and whatever extracts structured
requirements from a pasted job description.

The AI/data-science owner provides the production implementation (model,
catalogue matching, validation). The backend depends only on this interface
and validates everything a provider returns with JobDescriptionExtractionContent
below, so a provider cannot push unexpected fields through to storage.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SkillLabel = Field(min_length=1, max_length=120)
SkillCategory = Literal["technical", "soft"]

# Matches the AI team's own contract (job_description_extraction_contract.json):
# raw_text in, capped before it ever reaches a provider.
MAX_RAW_TEXT_CHARACTERS = 20000


class JobDescriptionExtractionProviderError(Exception):
    """Raised by a provider that cannot extract requirements from the text."""


@dataclass(frozen=True)
class JobDescriptionExtractionRequest:
    """Input for one extraction. Just the pasted text - no token, profile
    or session identifiers reach a provider."""

    raw_text: str


class ExtractedSkillContent(BaseModel):
    """One skill found in the job description."""

    model_config = ConfigDict(extra="forbid")

    label: str = SkillLabel
    category: SkillCategory


class JobDescriptionExtractionContent(BaseModel):
    """A validated extraction result returned by a provider.

    Exactly five fields, matching the AI team's contract - no score, no
    employability judgement, no field beyond what was agreed.
    """

    model_config = ConfigDict(extra="forbid")

    skills: list[ExtractedSkillContent] = Field(default_factory=list, max_length=40)
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    min_years_experience: int | None = Field(default=None, ge=0, le=60)
    keywords: list[str] = Field(default_factory=list, max_length=40)
    role_title_guess: str | None = Field(default=None, max_length=120)


class JobDescriptionExtractionProvider(ABC):
    """Extracts structured requirements from a pasted job description.

    Implementations return plain data (for example parsed model output);
    the backend validates it with JobDescriptionExtractionContent. Raise
    JobDescriptionExtractionProviderError when nothing suitable can be
    produced.
    """

    @abstractmethod
    def extract(self, request: JobDescriptionExtractionRequest) -> dict[str, Any]:
        """Return one extraction result matching JobDescriptionExtractionContent."""
        raise NotImplementedError
