from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.providers.scenario_provider import ActivityType

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
    trade_offs: list[str]
    areas_to_consider: list[str]
    skill_to_explore: SuggestedSkillResponse | None


class ScenarioOptionResponse(BaseModel):
    """One multiple-choice option. No option is labelled correct."""

    model_config = ConfigDict(from_attributes=True)

    option_id: str
    text: str


class ScenarioAttemptResponse(BaseModel):
    """The saved answer: selected_option_id for multiple choice, response_text
    for a written response. The other field is null."""

    model_config = ConfigDict(from_attributes=True)

    selected_option_id: str | None
    response_text: str | None
    submitted_at: datetime


class PracticeScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_id: str
    title: str
    workplace_area: str
    situation: str
    task: str
    activity_type: ActivityType
    options: list[ScenarioOptionResponse]  # empty for written_response
    guidance: list[str]
    skills_used: list[str]
    new_skill_focus: str | None
    status: Literal["upcoming", "current", "completed"]
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
    # False when her earlier activities could not be checked, so some of
    # these questions may be ones she has seen (AC 4.3.5 exception).
    history_checked: bool = True

    @field_validator("scenarios", mode="before")
    @classmethod
    def _hide_upcoming(cls, scenarios):
        """Questions she hasn't reached yet stay on the server, so the
        client can't show (or leak) what is coming next. progress still
        counts them in total_activities."""
        return [s for s in scenarios if getattr(s, "status", None) != "upcoming"]


class RecentActivityResponse(BaseModel):
    """One completed activity for the dashboard's "Recent practice" list
    (AC 3.4.1) - flattened out of whichever session it belongs to."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    activity_type: ActivityType
    completed_at: datetime
    session_id: str
    scenario_id: str
