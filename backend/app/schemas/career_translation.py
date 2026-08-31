from pydantic import BaseModel, ConfigDict


class OwnedSkillResponse(BaseModel):
    """One skill the user already has, with whether it is still in demand."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str
    still_relevant: bool


class NewHorizonSkillResponse(BaseModel):
    """One in-demand skill for the role that the user has not recorded."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str


class SkillRelevanceMapResponse(BaseModel):
    """API shape for the Skill Relevance Map: 'Skills You Bring Back' vs
    'New Horizons' for the user's previous role."""

    model_config = ConfigDict(from_attributes=True)
    role_label: str | None
    role_data_available: bool
    owned_skills: list[OwnedSkillResponse]
    custom_skills: list[str]
    new_horizons: list[NewHorizonSkillResponse]
