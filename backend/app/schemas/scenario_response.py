from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.practice_session import PracticeProgressResponse, PracticeScenarioResponse


class ScenarioResponseCreate(BaseModel):
    """POST body for a written scenario response.

    The text is stored as-is (outer whitespace trimmed) and is never executed.
    """

    model_config = ConfigDict(extra="forbid")

    response_text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
    ]


class ScenarioSubmissionResponse(BaseModel):
    """The answered scenario with its reflective feedback, plus updated progress."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    scenario: PracticeScenarioResponse
    progress: PracticeProgressResponse
