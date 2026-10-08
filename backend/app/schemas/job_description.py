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


class RefreshItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement: str
    profile_skill: str


class TransferableItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experience: str
    relates_to: str
    explanation: str


class JobComparisonResponse(BaseModel):
    """Her map for one job (AC 5.2.1). No score, percentage or verdict."""

    model_config = ConfigDict(from_attributes=True)

    job_description_id: str
    job_title: str | None
    experience_sentence: str | None
    break_start_year: int | None
    skills_bring_back: list[str]
    worth_refreshing: list[RefreshItemResponse]
    transferable_experience: list[TransferableItemResponse]
    skills_could_explore: list[str]


class RoleOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str
    role_label: str


class ClosestRolesResponse(BaseModel):
    """AC 5.2.2 - the roles closest to the job title, closest first."""

    model_config = ConfigDict(from_attributes=True)

    job_title: str | None
    exact_role_id: str | None
    closest: list[RoleOptionResponse]
    chosen_role_id: str | None


class ClosestRoleChoice(BaseModel):
    """PUT body: the role she chose as closest to a job description."""

    model_config = ConfigDict(extra="forbid")

    role_id: Annotated[str, StringConstraints(min_length=1, max_length=64)]


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
