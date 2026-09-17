from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Input caps (pen-test H-1, H-2). Text lengths follow the conventions in
# app/providers/scenario_provider.py: 120 (ShortText) for a label, 300
# (OptionText) for a one-sentence action, 500 (SentenceText) for a sentence.
# There is no min_length: ProfileService already trims these, turns blank
# "other" text into null and drops blank list entries, and that is kept.
CatalogueId = Annotated[str, StringConstraints(max_length=64)]  # catalogue ids are VARCHAR(64)
LabelInput = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]
ActionInput = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
SentenceInput = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

# Skills and responsibilities are picked one at a time, so 50 is well above
# normal use; typed-in entries are fewer.
MAX_SELECTED_IDS = 50
MAX_CUSTOM_ENTRIES = 20


class ProfileUpdate(BaseModel):
    """PATCH body for progressive profile capture.

    Every field is optional so the frontend can save one screen at a time.
    The service uses model_dump(exclude_unset=True) to tell "not sent" apart
    from "sent as null".
    """

    model_config = ConfigDict(extra="forbid")

    role_id: CatalogueId | None = None
    role_other_text: LabelInput | None = None  # job title for the "other" role
    years_experience: CatalogueId | None = None
    skill_ids: list[CatalogueId] | None = Field(default=None, max_length=MAX_SELECTED_IDS)
    custom_skills: list[LabelInput] | None = Field(default=None, max_length=MAX_CUSTOM_ENTRIES)
    responsibility_ids: list[CatalogueId] | None = Field(default=None, max_length=MAX_SELECTED_IDS)
    custom_responsibilities: list[ActionInput] | None = Field(
        default=None, max_length=MAX_CUSTOM_ENTRIES
    )
    break_reason: CatalogueId | None = None
    break_reason_other_text: SentenceInput | None = None
    break_started_on: date | None = None
    planned_return_date: date | None = None
    return_date_unsure: bool | None = None


class ProfileResponse(BaseModel):
    """API shape returned to the frontend for profile endpoints."""

    # Allows Pydantic to read fields from the internal Profile dataclass.
    model_config = ConfigDict(from_attributes=True)

    role_id: str | None
    role_other_text: str | None
    years_experience: str | None
    skill_ids: list[str]
    custom_skills: list[str]
    responsibility_ids: list[str]
    custom_responsibilities: list[str]
    break_reason: str | None
    break_reason_other_text: str | None
    break_started_on: date | None
    planned_return_date: date | None
    return_date_unsure: bool
    break_duration_months: int | None
    return_readiness: str | None
    area_to_explore: str | None
    confirmed: bool
