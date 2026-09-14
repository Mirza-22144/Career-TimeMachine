"""Boundary between the backend and whatever supplies workplace scenarios.

The AI/data-science owner provides the production implementation (model,
prompts, generation). The backend depends only on this interface and
validates everything a provider returns with the models below, so a provider
cannot push unexpected fields - such as a score - through to the user.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SentenceText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ScenarioProviderError(Exception):
    """Raised by a provider that cannot supply a scenario or feedback."""


@dataclass(frozen=True)
class ScenarioRequest:
    """Input for one scenario.

    Career context only: no token, profile or session identifiers, break
    details or free text the user typed.
    """

    role_id: str
    role_label: str
    years_experience: str | None
    skills: tuple[str, ...]
    responsibilities: tuple[str, ...]
    duration: str
    difficulty: str
    exclude_scenario_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeedbackRequest:
    """Input for reflective feedback on one submitted response."""

    role_label: str
    difficulty: str
    scenario_id: str
    situation: str
    task: str
    skills_used: tuple[str, ...]
    new_skill_focus: str | None
    response_text: str


class ScenarioContent(BaseModel):
    """A validated workplace scenario returned by a provider."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    title: ShortText
    workplace_area: ShortText
    situation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    task: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    # Written responses only this iteration; coding, MCQ and drag-and-drop
    # activity types can be added once their content contract is agreed.
    activity_type: Literal["written_response"]
    guidance: list[SentenceText] = Field(default_factory=list, max_length=5)
    skills_used: list[ShortText] = Field(default_factory=list, max_length=8)
    new_skill_focus: ShortText | None = None


class SkillToExplore(BaseModel):
    """A new or developing skill and why it matters for the scenario."""

    model_config = ConfigDict(extra="forbid")

    skill: ShortText
    why_relevant: SentenceText


# Wording that reads as a score, a pass/fail result or an employability
# judgement. Content guardrails are the AI owner's job; this is a backstop.
_JUDGEMENT_PATTERN = re.compile(
    r"\b(scored?|scores|grade[sd]?|pass(ed)?\s*/\s*fail(ed)?|you\s+(passed|failed)|"
    r"(not\s+)?employable|\d+\s*/\s*\d+|\d+\s+out\s+of\s+\d+)\b|\d{1,3}\s*%",
    re.IGNORECASE,
)


class FeedbackContent(BaseModel):
    """Validated reflective feedback.

    There is deliberately no field for a score, result or judgement, and
    wording that reads as one is rejected as invalid provider output.
    """

    model_config = ConfigDict(extra="forbid")

    what_worked_well: list[SentenceText] = Field(min_length=1, max_length=5)
    areas_to_consider: list[SentenceText] = Field(min_length=1, max_length=5)
    skill_to_explore: SkillToExplore | None = None

    @model_validator(mode="after")
    def _reject_judgements(self) -> "FeedbackContent":
        texts = [*self.what_worked_well, *self.areas_to_consider]
        if self.skill_to_explore is not None:
            texts += [self.skill_to_explore.skill, self.skill_to_explore.why_relevant]
        if any(_JUDGEMENT_PATTERN.search(text) for text in texts):
            raise ValueError("feedback must be reflective, without scores or pass/fail judgements")
        return self


class ScenarioProvider(ABC):
    """Supplies role-relevant scenarios and reflective feedback.

    Implementations return plain data (for example parsed model JSON); the
    backend validates it with ScenarioContent / FeedbackContent. Raise
    ScenarioProviderError when nothing suitable can be produced.
    """

    @abstractmethod
    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        """Return one scenario matching ScenarioContent."""
        raise NotImplementedError

    @abstractmethod
    def generate_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        """Return reflective feedback matching FeedbackContent."""
        raise NotImplementedError
