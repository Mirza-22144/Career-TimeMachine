from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.providers.scenario_provider import OptionId
from app.schemas.practice_session import PracticeProgressResponse, PracticeScenarioResponse

ANSWER_FIELDS = ("selected_option_id", "response_text", "placements")


class ScenarioResponseCreate(BaseModel):
    """POST body for a scenario response.

    Send exactly one field, matching the scenario's activity_type:
    selected_option_id (a single option) for multiple_choice, response_text
    for written_response, or placements (blank id -> phrase id, one phrase
    for each of the three blanks) for drag_and_drop. Text is stored as-is (outer whitespace trimmed) and
    nothing submitted is ever executed.
    """

    model_config = ConfigDict(extra="forbid")

    selected_option_id: OptionId | None = None
    response_text: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)] | None
    ) = None
    placements: dict[Annotated[str, StringConstraints(pattern=r"^blank_[1-3]$")], OptionId] | None = Field(
        default=None, max_length=3
    )

    @model_validator(mode="after")
    def _exactly_one_answer(self) -> "ScenarioResponseCreate":
        sent = [name for name in ANSWER_FIELDS if name in self.model_fields_set]
        if len(sent) != 1 or getattr(self, sent[0]) is None:
            raise ValueError("send exactly one of selected_option_id, response_text or placements")
        return self


class ScenarioSubmissionResponse(BaseModel):
    """The answered scenario with its reflective feedback, plus updated progress."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    scenario: PracticeScenarioResponse
    progress: PracticeProgressResponse
