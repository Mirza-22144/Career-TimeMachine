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
OptionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
OptionId = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")]

# How the user completes a scenario. Iteration 2 serves multiple_choice;
# written_response stays supported for later iterations.
ActivityType = Literal["multiple_choice", "written_response"]


class ScenarioProviderError(Exception):
    """Raised by a provider that cannot supply a scenario or feedback."""


@dataclass(frozen=True)
class ScenarioRequest:
    """Input for one scenario.

    Career context only: no token, profile or session identifiers, break
    details, or custom skills/responsibilities the user typed. The one
    exception is role_label for the "other" previous role, which is the job
    title the user entered.
    """

    role_id: str
    role_label: str
    years_experience: str | None
    skills: tuple[str, ...]
    responsibilities: tuple[str, ...]
    duration: str
    difficulty: str
    activity_type: str  # an ActivityType; the provider must return this type
    exclude_scenario_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeedbackRequest:
    """Input for reflective feedback on one submitted response.

    multiple_choice sets selected_option_id and selected_option_text, with
    every option's text in option_texts; written_response sets response_text.
    """

    role_label: str
    difficulty: str
    scenario_id: str
    situation: str
    task: str
    skills_used: tuple[str, ...]
    new_skill_focus: str | None
    activity_type: str
    response_text: str | None = None
    selected_option_id: str | None = None
    selected_option_text: str | None = None
    option_texts: tuple[str, ...] = ()


class ScenarioOptionContent(BaseModel):
    """One choice in a multiple-choice scenario.

    There is deliberately no field marking an option as correct: each option
    is a plausible workplace approach with its own trade-offs.
    """

    model_config = ConfigDict(extra="forbid")

    option_id: OptionId
    text: OptionText


class ScenarioContent(BaseModel):
    """A validated workplace scenario returned by a provider.

    situation is the workplace context and task is the question or decision
    prompt. A multiple_choice scenario has 2-6 options with unique ids and the
    user selects exactly one; a written_response scenario has no options.
    """

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    title: ShortText
    workplace_area: ShortText
    situation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    task: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    # Coding and drag-and-drop types can be added once their contract is agreed.
    activity_type: ActivityType
    options: list[ScenarioOptionContent] = Field(default_factory=list, max_length=6)
    guidance: list[SentenceText] = Field(default_factory=list, max_length=5)
    skills_used: list[ShortText] = Field(default_factory=list, max_length=8)
    new_skill_focus: ShortText | None = None

    @model_validator(mode="after")
    def _check_options_match_activity_type(self) -> "ScenarioContent":
        if self.activity_type == "written_response":
            if self.options:
                raise ValueError("a written_response scenario must not have options")
            return self
        if len(self.options) < 2:
            raise ValueError("a multiple_choice scenario needs at least two options")
        option_ids = [option.option_id for option in self.options]
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("option ids must be unique within a scenario")
        return self


class SkillToExplore(BaseModel):
    """A new or developing skill and why it matters for the scenario."""

    model_config = ConfigDict(extra="forbid")

    skill: ShortText
    why_relevant: SentenceText


# Wording that reads as a score, a pass/fail result, a correct/incorrect label,
# a readiness gauge or an employability judgement. Content guardrails are the
# AI owner's job; this is a backstop.
_JUDGEMENT_PATTERN = re.compile(
    r"\b(scored?|scores|grade[sd]?|pass(ed)?\s*/\s*fail(ed)?|you\s+(passed|failed)|"
    r"(not\s+)?employable|employability|(in)?correct|(right|wrong)\s+(answer|choice|option)|"
    r"readiness\s+(score|gauge|level|rating)|\d+\s*/\s*\d+|\d+\s+out\s+of\s+\d+)\b|\d{1,3}\s*%",
    re.IGNORECASE,
)


class FeedbackContent(BaseModel):
    """Validated reflective feedback.

    There is deliberately no field for a score, result or judgement, and
    wording that reads as one is rejected as invalid provider output.
    """

    model_config = ConfigDict(extra="forbid")

    # For multiple choice: why the selected option may be useful.
    what_worked_well: list[SentenceText] = Field(min_length=1, max_length=5)
    # Workplace trade-offs of the chosen approach. Expected for multiple
    # choice; optional for written responses.
    trade_offs: list[SentenceText] = Field(default_factory=list, max_length=5)
    # Other considerations, such as what the other options would offer.
    areas_to_consider: list[SentenceText] = Field(min_length=1, max_length=5)
    skill_to_explore: SkillToExplore | None = None

    @model_validator(mode="after")
    def _reject_judgements(self) -> "FeedbackContent":
        texts = [*self.what_worked_well, *self.trade_offs, *self.areas_to_consider]
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
