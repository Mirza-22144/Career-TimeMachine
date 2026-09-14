from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

DURATION_MINUTES = {"quick": 5, "standard": 10, "challenge": 15}


@dataclass
class SuggestedSkill:
    """A new or developing skill the user could explore next."""

    skill: str
    why_relevant: str


@dataclass
class ReflectiveFeedback:
    """Reflective feedback on one response. There is no score, pass/fail
    result or judgement, by design."""

    what_worked_well: list[str]
    areas_to_consider: list[str]
    skill_to_explore: SuggestedSkill | None = None


@dataclass
class ScenarioAttempt:
    """The user's submitted response, stored as text only."""

    response_text: str
    submitted_at: datetime


@dataclass
class PracticeScenario:
    """One workplace scenario inside a practice session."""

    scenario_id: str
    title: str
    workplace_area: str
    situation: str
    task: str
    activity_type: str
    guidance: list[str]
    skills_used: list[str]
    new_skill_focus: str | None
    status: str = "current"  # "current" | "completed"
    response: ScenarioAttempt | None = None
    feedback: ReflectiveFeedback | None = None
    # Once a response exists: "available", or "unavailable" if feedback
    # could not be generated.
    feedback_status: str | None = None


@dataclass
class PracticeRoleRef:
    """The saved practice role copied onto the session when it started."""

    id: str
    label: str
    source: str


@dataclass
class PracticeProgress:
    """Where the user is in a practice session."""

    status: str
    total_activities: int
    completed_activities: int
    current_scenario_id: str | None


@dataclass
class PracticeSession:
    """A workplace-practice session owned by one anonymous session.

    Plain internal data, not a database model. The owner is the token hash,
    the same key used for profiles.
    """

    session_id: str
    owner_token_hash: str
    role: PracticeRoleRef
    duration: str  # "quick" | "standard" | "challenge"
    difficulty: str  # "guided" | "standard" | "challenge"
    status: str  # "active" | "completed" | "abandoned"
    created_at: datetime
    updated_at: datetime
    scenarios: list[PracticeScenario] = field(default_factory=list)
    completed_at: datetime | None = None

    @property
    def duration_minutes(self) -> int:
        return DURATION_MINUTES[self.duration]

    @property
    def progress(self) -> PracticeProgress:
        completed = sum(1 for scenario in self.scenarios if scenario.status == "completed")
        current = next(
            (scenario.scenario_id for scenario in self.scenarios if scenario.status == "current"),
            None,
        )
        return PracticeProgress(
            status=self.status,
            total_activities=len(self.scenarios),
            completed_activities=completed,
            current_scenario_id=current if self.status == "active" else None,
        )


class PracticeSessionRepository(ABC):
    """Storage contract for practice sessions, their scenarios, responses
    and feedback. Every read is scoped to the owning token hash."""

    @abstractmethod
    def add(self, session: PracticeSession) -> PracticeSession:
        """Save a new practice session."""
        raise NotImplementedError

    @abstractmethod
    def get_for_owner(self, owner_token_hash: str, session_id: str) -> PracticeSession | None:
        """Return the session only if it exists and belongs to this owner."""
        raise NotImplementedError

    @abstractmethod
    def get_active_for_owner(self, owner_token_hash: str) -> PracticeSession | None:
        """Return the owner's most recently started active session, if any."""
        raise NotImplementedError

    @abstractmethod
    def save(self, session: PracticeSession) -> PracticeSession:
        """Replace the stored state of an existing session."""
        raise NotImplementedError
