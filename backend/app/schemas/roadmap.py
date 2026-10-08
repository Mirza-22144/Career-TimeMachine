from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.predicted_roles import MarketDataResponse


class RoadmapSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None
    label: str


class ExploreSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    status: Literal["practised", "next", "later"]
    practised_on: datetime | None


class RoadmapRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str
    role_label: str
    skill_data_available: bool
    skills_bring_back: list[RoadmapSkillResponse]
    skills_could_explore: list[ExploreSkillResponse]
    market_data: MarketDataResponse | None


class RoadmapResponse(BaseModel):
    """Your Roadmap (AC 2.2.3/2.2.4). No scores or percentages by design."""

    model_config = ConfigDict(from_attributes=True)

    previous_role: RoadmapRoleResponse | None
    years_experience_label: str | None
    suggested_roles: list[RoadmapRoleResponse]
    selected_role_id: str | None
