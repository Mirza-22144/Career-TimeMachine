from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.providers.job_description_extraction_provider import MAX_RAW_TEXT_CHARACTERS

# 150-character minimum matches AC 5.1.1's exception condition ("This looks
# too short to be a full job description") - the frontend enforces this
# client-side before ever submitting, this is the real backstop.
MIN_RAW_TEXT_CHARACTERS = 150

RawText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=MIN_RAW_TEXT_CHARACTERS, max_length=MAX_RAW_TEXT_CHARACTERS
    ),
]


class JobDescriptionCreate(BaseModel):
    """POST body for pasting a job description (AC Step 3, Path 1 only)."""

    model_config = ConfigDict(extra="forbid")

    raw_text: RawText


class ExtractedSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    category: Literal["technical", "soft"]


class JobDescriptionResponse(BaseModel):
    """API shape for one job description and its extracted requirements."""

    model_config = ConfigDict(from_attributes=True)

    job_description_id: str
    raw_text: str
    extracted_skills: list[ExtractedSkillResponse]
    extracted_responsibilities: list[str]
    min_years_experience: int | None
    keywords: list[str]
    role_title_guess: str | None
    created_at: datetime
