from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

PracticeDuration = Literal["quick", "standard", "challenge"]
PracticeDifficulty = Literal["guided", "standard", "challenge"]


class PracticeSessionCreate(BaseModel):
    """POST body for starting workplace practice (AC 4.2.2).

    Duration and difficulty are separate required choices. The role is not
    sent: it comes from the saved practice role.
    """

    model_config = ConfigDict(extra="forbid")

    duration: PracticeDuration
    difficulty: PracticeDifficulty


class PracticeRoleRefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    source: Literal["previous", "predicted"]


class SuggestedSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill: str
    why_relevant: str


class ReflectiveFeedbackResponse(BaseModel):
    """Reflective feedback. Deliberately has no score or result field."""

    model_config = ConfigDict(from_attributes=True)

    what_worked_well: list[str]
    areas_to_consider: list[str]
    skill_to_explore: SuggestedSkillResponse | None


class ScenarioAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_text: str
    submitted_at: datetime


class PracticeScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_id: str
    title: str
    workplace_area: str
    situation: str
    task: str
    activity_type: str
    guidance: list[str]
    skills_used: list[str]
    new_skill_focus: str | None
    status: Literal["current", "completed"]
    response: ScenarioAttemptResponse | None
    feedback: ReflectiveFeedbackResponse | None
    feedback_status: Literal["available", "unavailable"] | None


class PracticeProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["active", "completed", "abandoned"]
    total_activities: int
    completed_activities: int
    current_scenario_id: str | None


class PracticeSessionResponse(BaseModel):
    """A practice session with its scenarios and progress. The owner is
    never included."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    role: PracticeRoleRefResponse
    duration: PracticeDuration
    duration_minutes: int
    difficulty: PracticeDifficulty
    status: Literal["active", "completed", "abandoned"]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    scenarios: list[PracticeScenarioResponse]
    progress: PracticeProgressResponse
