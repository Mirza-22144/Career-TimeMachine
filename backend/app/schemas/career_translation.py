from pydantic import BaseModel, ConfigDict


class OwnedSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str
    still_relevant: bool


class NewHorizonSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str


class SkillRelevanceMapResponse(BaseModel):
    """AC 2.2.1: 'Skills You Bring Back' vs 'New Horizons' for the user's
    previous role - not a skill-to-career-area mapping."""

    model_config = ConfigDict(from_attributes=True)
    role_label: str | None
    role_data_available: bool
    owned_skills: list[OwnedSkillResponse]
    custom_skills: list[str]
    new_horizons: list[NewHorizonSkillResponse]
