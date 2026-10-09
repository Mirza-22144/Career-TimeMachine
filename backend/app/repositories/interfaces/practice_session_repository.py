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
    trade_offs: list[str] = field(default_factory=list)


@dataclass
class ScenarioOption:
    """One choice in a multiple-choice scenario. No option is marked correct."""

    option_id: str
    text: str


@dataclass
class ScenarioAttempt:
    """The user's submitted answer, stored as data and never executed.

    Multiple choice sets selected_option_id; a written response sets
    response_text; drag and drop sets placements (blank id -> the id of the
    phrase she put there). The other fields stay None.
    """

    submitted_at: datetime
    response_text: str | None = None
    selected_option_id: str | None = None
    placements: dict | None = None


@dataclass
class PracticeScenario:
    """One workplace scenario inside a practice session."""

    scenario_id: str
    title: str
    workplace_area: str
    situation: str
    task: str
    activity_type: str  # "multiple_choice" | "written_response" | "drag_and_drop"
    guidance: list[str]
    skills_used: list[str]
    new_skill_focus: str | None
    # Two or more for multiple_choice, empty for written_response.
    options: list[ScenarioOption] = field(default_factory=list)
    # "upcoming" (not reached yet) | "current" | "completed". An activity's
    # questions are answered one at a time, so exactly one is current.
    status: str = "current"
    response: ScenarioAttempt | None = None
    feedback: ReflectiveFeedback | None = None
    # Once a response exists: "available", or "unavailable" if feedback
    # could not be generated.
    feedback_status: str | None = None
    # Live questions only: option id -> reflective feedback, kept with the
    # scenario because there is no pool to look it up in. Never sent to the
    # client as a whole - only the chosen option's feedback is, after she answers.
    option_feedback: dict | None = None
    # Drag and drop only, and never sent to the client as it is:
    # {"sentence_template", "fits": phrase id -> the blank it is meant for
    # (or None), "feedback_by_option": phrase id -> {"why", "what_to_improve"}}.
    content: dict | None = None

    @property
    def sentence_template(self) -> str | None:
        """The message with its {blank_1}..{blank_3} gaps (drag and drop)."""
        return self.content.get("sentence_template") if self.content else None

    @property
    def phrase_feedback(self) -> list[dict] | None:
        """Drag and drop, once she has submitted: how each phrase she placed
        comes across, in the order of the gaps. "what_would_work_better" is
        only set for a phrase that does not fit where she put it - nothing
        is ever labelled right or wrong, and nothing is counted."""
        if not self.content or self.response is None or not self.response.placements:
            return None
        texts = {option.option_id: option.text for option in self.options}
        fits = self.content.get("fits", {})
        feedback = self.content.get("feedback_by_option", {})
        phrases = []
        for blank_id in sorted(self.response.placements):
            option_id = self.response.placements[blank_id]
            entry = feedback.get(option_id, {})
            better = entry.get("what_to_improve")
            meant_for = fits.get(option_id)
            if better is None and meant_for is not None and meant_for != blank_id:
                better = "This phrase reads more naturally in a different gap of the message."
            phrases.append(
                {
                    "blank_id": blank_id,
                    "option_id": option_id,
                    "text": texts.get(option_id, ""),
                    "comes_across": entry.get("why", ""),
                    "what_would_work_better": better,
                }
            )
        return phrases

    @property
    def completed_message(self) -> str | None:
        """Her finished message (drag and drop, once submitted)."""
        if not self.content or self.response is None or not self.response.placements:
            return None
        texts = {option.option_id: option.text for option in self.options}
        message = self.content.get("sentence_template", "")
        for blank_id, option_id in self.response.placements.items():
            message = message.replace("{" + blank_id + "}", texts.get(option_id, ""))
        return message


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
    # False only on the response to starting an activity when her earlier
    # sessions could not be read, so questions may repeat (AC 4.3.5). Not
    # stored.
    history_checked: bool = True
    # The skill to explore this activity's first question uses, told to her
    # on the preparation page. Only on the response to starting; not stored.
    focus_skill: str | None = None

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

    @abstractmethod
    def list_for_owner(self, owner_token_hash: str) -> list[PracticeSession]:
        """Return every session this owner has started, in no particular
        order (callers that care about ordering, like the dashboard's
        recent-activity list, sort by whatever they need)."""
        raise NotImplementedError

    def add_scenario(self, owner_token_hash: str, session_id: str, scenario: PracticeScenario) -> bool:
        """Add one more upcoming question to a session that is still active
        and still has a question open, without touching the others (they may
        be being answered at the same moment). Return False if the session
        is no longer in that state, in which case nothing is added."""
        raise NotImplementedError
