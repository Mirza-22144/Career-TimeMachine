from datetime import date

from pydantic import BaseModel, ConfigDict


class ProfileUpdate(BaseModel):
    """PATCH body for progressive profile capture.

    Every field is optional so the frontend can save one screen at a time.
    The service uses model_dump(exclude_unset=True) to tell "not sent" apart
    from "sent as null".
    """

    role_id: str | None = None
    role_other_text: str | None = None
    years_experience: str | None = None
    skill_ids: list[str] | None = None
    custom_skills: list[str] | None = None
    responsibility_ids: list[str] | None = None
    custom_responsibilities: list[str] | None = None
    break_reason: str | None = None
    break_reason_other_text: str | None = None
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
    confirmed: bool
