from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.providers.scenario_provider import OptionId
from app.schemas.practice_session import PracticeProgressResponse, PracticeScenarioResponse

ANSWER_FIELDS = ("selected_option_id", "response_text")


class ScenarioResponseCreate(BaseModel):
    """POST body for a scenario response.

    Send exactly one field, matching the scenario's activity_type:
    selected_option_id (a single option) for multiple_choice, or response_text
    for written_response. Text is stored as-is (outer whitespace trimmed) and
    nothing submitted is ever executed.
    """

    model_config = ConfigDict(extra="forbid")

    selected_option_id: OptionId | None = None
    response_text: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)] | None
    ) = None

    @model_validator(mode="after")
    def _exactly_one_answer(self) -> "ScenarioResponseCreate":
        sent = [name for name in ANSWER_FIELDS if name in self.model_fields_set]
        if len(sent) != 1 or getattr(self, sent[0]) is None:
            raise ValueError("send exactly one of selected_option_id or response_text")
        return self


class ScenarioSubmissionResponse(BaseModel):
    """The answered scenario with its reflective feedback, plus updated progress."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    scenario: PracticeScenarioResponse
    progress: PracticeProgressResponse
