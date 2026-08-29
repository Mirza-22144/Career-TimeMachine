from datetime import date

from pydantic import BaseModel, ConfigDict


class CatalogueSelectionResponse(BaseModel):
    """A selected catalogue item after its user-facing label is resolved."""

    # Lets Pydantic read from the dataclass returned by the service.
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str


class CareerBreakResponse(BaseModel):
    """Career break timing summary shown in the journey output."""

    # Lets Pydantic read from the dataclass returned by the service.
    model_config = ConfigDict(from_attributes=True)

    break_started_on: date | None
    planned_return_date: date | None
    return_date_unsure: bool
    break_duration_months: int | None


class SelectedSkillsResponse(BaseModel):
    """Selected catalogue skills plus custom skill labels."""

    # Lets Pydantic read from the dataclass returned by the service.
    model_config = ConfigDict(from_attributes=True)

    catalogue_skills: list[CatalogueSelectionResponse]
    custom_skills: list[str]


class CareerJourneyResponse(BaseModel):
    """Structured, frontend-ready career journey summary."""

    # Lets Pydantic read the top-level dataclass and nested dataclasses.
    model_config = ConfigDict(from_attributes=True)

    previous_role: CatalogueSelectionResponse | None
    years_experience: CatalogueSelectionResponse | None
    career_break: CareerBreakResponse
    current_return_status: CatalogueSelectionResponse | None
    selected_skills: SelectedSkillsResponse
    strengths: list[str]
