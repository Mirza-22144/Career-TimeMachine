import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.providers.live_question_provider import LiveQuestion, LiveQuestionProvider
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.providers.drag_and_drop_provider import DragDropProvider
from app.providers.scenario_provider import (
    ScenarioContent,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)
from app.repositories.interfaces.practice_session_repository import (
    PracticeRoleRef,
    PracticeScenario,
    PracticeSession,
    PracticeSessionRepository,
    ScenarioOption,
)
from app.schemas.practice_session import PracticeSessionCreate
from app.services.practice_role_service import PracticeContext, PracticeRoleService

logger = logging.getLogger(__name__)

RequestT = TypeVar("RequestT")

# Provider calls run on worker threads so a slow provider can be abandoned
# after a timeout instead of holding the request open.
_provider_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="scenario-provider")


def call_provider(
    func: Callable[[RequestT], Any],
    request: RequestT,
    timeout_seconds: float,
) -> Any:
    """Run one provider call with a timeout. Every failure, including a
    timeout or an unexpected exception, becomes ScenarioProviderError."""
    future = _provider_executor.submit(func, request)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise ScenarioProviderError("provider timed out") from exc
    except ScenarioProviderError:
        raise
    except Exception as exc:
        raise ScenarioProviderError("provider failed") from exc


def practice_error(status_code: int, code: str, message: str) -> HTTPException:
    """Build a structured error for core/exceptions.py to wrap."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Dashboard's "Recent practice" list (AC 3.4.1) shows at most this many,
# newest first - no pagination asked for, just a cap so a long history
# doesn't grow the response unboundedly.
MAX_RECENT_ACTIVITIES = 10


@dataclass
class RecentActivity:
    """One completed activity, flattened out of its practice session for
    the dashboard - a session can hold several, each possibly a different
    type. completed_at comes from the response itself (when she actually
    submitted it), not the session's own timestamps."""

    title: str
    activity_type: str
    completed_at: datetime
    # Where its feedback can be read again (GET /practice-sessions/{id}).
    session_id: str
    scenario_id: str


class PracticeSessionService:
    """Starts, retrieves and completes workplace-practice sessions."""

    def __init__(
        self,
        sessions: PracticeSessionRepository,
        practice_roles: PracticeRoleService,
        provider: ScenarioProvider,
        provider_timeout_seconds: float = 10.0,
        activity_type: str = "multiple_choice",
        questions_per_activity: int = 1,
        live_questions: LiveQuestionProvider | None = None,
        live_timeout_seconds: float = 8.0,
        catalogue: CatalogueRepository | None = None,
        run_in_background: Callable[[Callable[[], None]], None] | None = None,
        drag_drop: DragDropProvider | None = None,
    ) -> None:
        # Storage and scenario generation are both behind interfaces, so the
        # database and AI implementations can be swapped in without changes here.
        self.sessions = sessions
        self.practice_roles = practice_roles
        self.provider = provider
        self.provider_timeout_seconds = provider_timeout_seconds
        # The interaction new scenarios use (multiple_choice or written_response).
        self.activity_type = activity_type
        # How many pre-written questions one activity serves, and the
        # optional provider of one extra live question about a skill she
        # typed in herself (Iteration 3: four static + one live).
        self.questions_per_activity = questions_per_activity
        self.live_questions = live_questions
        self.live_timeout_seconds = live_timeout_seconds
        # Used to put questions about her practice focus first (AC 4.4.5).
        self.catalogue = catalogue
        # When set, the live question is written after the activity has
        # started instead of making her wait for it: it is added to the
        # session as soon as it is ready, well before she reaches it.
        self.run_in_background = run_in_background
        # Drag and Drop activities (US 4.6). None means they are not offered.
        self.drag_drop = drag_drop

    def start_session(self, owner: str, settings: PracticeSessionCreate) -> PracticeSession:
        """Start one activity with the saved role, saved career context and
        the chosen settings: up to questions_per_activity pre-written
        questions she has not answered before, plus one live question when
        she has typed in a skill of her own. Nothing is stored if no
        question can be prepared.

        An activity has to be finished before another one starts, so earlier
        practice is never replaced: an unfinished one is refused with 409,
        and one whose questions are all answered is closed as completed."""
        now = utc_now()
        previous = self.sessions.get_active_for_owner(owner)
        if previous is not None:
            if previous.progress.current_scenario_id is not None:
                raise practice_error(
                    status.HTTP_409_CONFLICT,
                    "ACTIVITY_IN_PROGRESS",
                    "Finish your current activity before starting a new one",
                )
            previous.status = "completed"
            previous.completed_at = now
            previous.updated_at = now
            self.sessions.save(previous)

        context = self.practice_roles.build_practice_context(owner)
        # AC 4.3.5 exception: if her earlier activities cannot be checked she
        # still practises - some questions may repeat, and the response says so.
        history_checked = True
        try:
            earlier = self.sessions.list_for_owner(owner)
        except HTTPException:
            logger.warning("Earlier practice could not be checked; questions may repeat")
            earlier, history_checked = [], False
        answered = self._answered(earlier, context.role_id, settings.difficulty)
        is_drag_drop = settings.activity_type == "drag_and_drop"
        if is_drag_drop:
            scenarios = self._new_drag_drop(context, settings.difficulty, answered)
        else:
            scenarios = self._new_questions(context, settings.duration, settings.difficulty, answered)
        if not scenarios:
            raise practice_error(
                status.HTTP_409_CONFLICT,
                "NO_NEW_ACTIVITIES",
                "You have completed all the activities for this role at this level",
            )
        exclude = answered | {scenario.scenario_id for scenario in scenarios}
        focus_skill = self._put_focus_first(scenarios, context, earlier)

        # One more, about a skill she typed in herself. Written inline here,
        # or off the request when a background runner is set.
        if is_drag_drop:
            wants_live = self.drag_drop is not None and bool(context.custom_skills)

            def make_live() -> PracticeScenario | None:
                return self._live_drag_drop(context, settings.difficulty)
        else:
            wants_live = self.live_questions is not None and bool(context.custom_skills)
            role_id, difficulty, skills = context.role_id, settings.difficulty, list(context.custom_skills)

            def make_live() -> PracticeScenario | None:
                return self._live_question(role_id, difficulty, skills, exclude)

        if wants_live and self.run_in_background is None:
            live = make_live()
            if live is not None:
                scenarios.append(live)

        for index, scenario in enumerate(scenarios):
            scenario.status = "current" if index == 0 else "upcoming"

        session_id = uuid.uuid4().hex
        started = self.sessions.add(
            PracticeSession(
                session_id=session_id,
                owner_token_hash=owner,
                role=PracticeRoleRef(
                    id=context.role_id,
                    label=context.role_label,
                    source=context.role_source,
                ),
                duration=settings.duration,
                difficulty=settings.difficulty,
                status="active",
                created_at=now,
                updated_at=now,
                scenarios=scenarios,
                history_checked=history_checked,
                focus_skill=focus_skill,
            )
        )
        if wants_live and self.run_in_background is not None:
            self.run_in_background(lambda: self._add_live_question(owner, session_id, make_live))
        return started

    def _new_drag_drop(self, context: PracticeContext, difficulty: str, answered: set[str]) -> list[PracticeScenario]:
        """Up to questions_per_activity pre-written Drag and Drop activities
        she has not done for this role and difficulty."""
        if self.drag_drop is None:
            return []
        return [
            self._to_drag_drop_scenario(fields)
            for fields in self.drag_drop.static_activities(
                context.role_id, difficulty, answered, self.questions_per_activity
            )
        ]

    def _live_drag_drop(self, context: PracticeContext, difficulty: str) -> PracticeScenario | None:
        """One Drag and Drop activity about a skill she typed in herself, or
        None when it cannot be produced in time. Never fails the session."""
        try:
            fields = call_provider(
                lambda skills: self.drag_drop.live_activity(
                    context.role_id, difficulty, skills, context.years_experience, list(context.responsibilities)
                ),
                list(context.custom_skills),
                self.live_timeout_seconds,
            )
        except ScenarioProviderError as exc:
            logger.warning("Live drag-and-drop activity unavailable (%s)", type(exc).__name__)
            return None
        return self._to_drag_drop_scenario(fields) if fields is not None else None

    @staticmethod
    def _to_drag_drop_scenario(fields: dict) -> PracticeScenario:
        return PracticeScenario(
            **{key: value for key, value in fields.items() if key != "options"},
            options=[ScenarioOption(option_id=o["option_id"], text=o["text"]) for o in fields["options"]],
        )

    def _add_live_question(self, owner: str, session_id: str, make_live: Callable[[], PracticeScenario | None]) -> None:
        """Write the live question and add it as the last question of an
        activity that has already started. Runs off the request; any failure
        just means the activity keeps its pre-written questions."""
        try:
            live = make_live()
            if live is None:
                return
            live.status = "upcoming"
            if not self.sessions.add_scenario(owner, session_id, live):
                logger.info("Live question arrived after the activity had finished; not added")
        except Exception as exc:  # noqa: BLE001 - a background task must never raise
            logger.warning("Live question could not be added (%s)", type(exc).__name__)

    def _put_focus_first(
        self, scenarios: list[PracticeScenario], context: PracticeContext, earlier: list[PracticeSession]
    ) -> str | None:
        """AC 4.4.5: questions that use her practice focus come first.
        Returns the focus this activity really uses, or None when it uses
        none of the skills left for her to explore.

        The order of focus is the roadmap's (RoadmapService._explore_steps):
        skills of the role she doesn't have and hasn't practised, in
        catalogue order. Questions that use none of them keep their order."""
        if self.catalogue is None or not scenarios:
            return None
        owned = {label.casefold() for label in context.skills}
        practised = {
            label.casefold()
            for session in earlier
            if session.role.id == context.role_id
            for scenario in session.scenarios
            if scenario.status == "completed"
            for label in scenario.skills_used
        }
        in_activity = {skill.casefold() for scenario in scenarios for skill in scenario.skills_used}
        focus = [
            skill.label
            for skill in self.catalogue.get_skills_for_role(context.role_id)
            if skill.label.casefold() in in_activity
            and skill.label.casefold() not in owned
            and skill.label.casefold() not in practised
        ]
        rank = {label.casefold(): index for index, label in reversed(list(enumerate(focus)))}

        def position(scenario: PracticeScenario) -> int:
            return min((rank[s.casefold()] for s in scenario.skills_used if s.casefold() in rank), default=len(focus))

        scenarios.sort(key=position)  # stable: ties keep the pool's order
        return focus[0] if focus else None

    def get_session(self, owner: str, session_id: str) -> PracticeSession:
        """Return one of the owner's sessions. Another user's session gets
        the same 404 as a session that does not exist."""
        session = self.sessions.get_for_owner(owner, session_id)
        if session is None:
            raise practice_error(
                status.HTTP_404_NOT_FOUND,
                "PRACTICE_SESSION_NOT_FOUND",
                "Practice session not found",
            )
        return session

    def remaining_by_difficulty(self, owner: str) -> dict[str, dict[str, int]]:
        """How many pre-written questions she has not answered yet for her
        practice role, per kind of activity and difficulty (capped at one
        activity's worth). The practice screens use it to know what can
        still be unlocked without preparing anything."""
        context = self.practice_roles.build_practice_context(owner)
        sessions = self.sessions.list_for_owner(owner)
        remaining: dict[str, dict[str, int]] = {"multiple_choice": {}, "drag_and_drop": {}}
        for difficulty in ("guided", "standard", "challenge"):
            answered = self._answered(sessions, context.role_id, difficulty)
            remaining["multiple_choice"][difficulty] = len(
                self._new_questions(context, "standard", difficulty, answered)
            )
            remaining["drag_and_drop"][difficulty] = len(self._new_drag_drop(context, difficulty, answered))
        return remaining

    @staticmethod
    def _answered(sessions: list[PracticeSession], role_id: str, difficulty: str) -> set[str]:
        """AC 4.3.5: every question she has already answered for this role
        and difficulty - across every earlier session."""
        return {
            scenario.scenario_id
            for session in sessions
            if session.role.id == role_id and session.difficulty == difficulty
            for scenario in session.scenarios
            if scenario.status == "completed"
        }

    def _new_questions(
        self, context: PracticeContext, duration: str, difficulty: str, answered: set[str]
    ) -> list[PracticeScenario]:
        """Up to questions_per_activity pre-written questions not in
        `answered`. Empty when she has answered them all; a provider failure
        with nothing answered before is a real error and is raised."""
        scenarios: list[PracticeScenario] = []
        exclude = set(answered)
        for _ in range(self.questions_per_activity):
            try:
                scenario = self._generate_scenario(
                    ScenarioRequest(
                        role_id=context.role_id,
                        role_label=context.role_label,
                        skills=tuple(context.skills),
                        duration=duration,
                        difficulty=difficulty,
                        activity_type=self.activity_type,
                        exclude_scenario_ids=tuple(sorted(exclude)),
                    )
                )
            except HTTPException:
                if scenarios or answered:
                    break  # simply no more questions
                raise
            if scenario.scenario_id in exclude:
                break  # a provider that ignores exclusions has nothing new
            scenarios.append(scenario)
            exclude.add(scenario.scenario_id)
        return scenarios

    def get_current_session(self, owner: str) -> PracticeSession:
        """Return the owner's active session so practice can be resumed."""
        session = self.sessions.get_active_for_owner(owner)
        if session is None:
            raise practice_error(
                status.HTTP_404_NOT_FOUND,
                "PRACTICE_SESSION_NOT_FOUND",
                "No active practice session",
            )
        return session

    def list_recent_activities(self, owner: str) -> list[RecentActivity]:
        """AC 3.4.1: every completed activity across all of the owner's
        sessions, newest first, capped at MAX_RECENT_ACTIVITIES. Only
        scenarios that were actually submitted count - a scenario marked
        'completed' with no response (shouldn't happen, but never assume)
        has nothing to date it by and is skipped rather than guessed at."""
        activities = [
            RecentActivity(
                title=scenario.title,
                activity_type=scenario.activity_type,
                completed_at=scenario.response.submitted_at,
                session_id=session.session_id,
                scenario_id=scenario.scenario_id,
            )
            for session in self.sessions.list_for_owner(owner)
            for scenario in session.scenarios
            if scenario.status == "completed" and scenario.response is not None
        ]
        activities.sort(key=lambda activity: activity.completed_at, reverse=True)
        return activities[:MAX_RECENT_ACTIVITIES]

    def complete_session(self, owner: str, session_id: str) -> PracticeSession:
        """Mark an active session completed. Completing twice is harmless."""
        session = self.get_session(owner, session_id)
        if session.status == "completed":
            return session
        if session.status != "active":
            raise practice_error(
                status.HTTP_409_CONFLICT,
                "PRACTICE_SESSION_NOT_ACTIVE",
                "Practice session is no longer active",
            )

        now = utc_now()
        session.status = "completed"
        session.completed_at = now
        session.updated_at = now
        return self.sessions.save(session)

    def _live_question(
        self, role_id: str, difficulty: str, custom_skills: list[str], exclude: set[str]
    ) -> PracticeScenario | None:
        """One question about a skill she typed in herself (AC 4.4.6), or
        None when she has none or nothing valid comes back. Never fails the
        session: a slow or broken generator simply means no extra question
        (the provider itself already falls back to a static one)."""
        if self.live_questions is None or not custom_skills:
            return None
        try:
            result: LiveQuestion | None = call_provider(
                lambda skills: self.live_questions.generate(role_id, difficulty, skills),
                custom_skills,
                self.live_timeout_seconds,
            )
            if result is None or result.scenario["scenario_id"] in exclude:
                return None
            content = ScenarioContent.model_validate(result.scenario)
        except (ScenarioProviderError, ValidationError) as exc:
            logger.warning("Live question unavailable (%s)", type(exc).__name__)
            return None

        return PracticeScenario(
            **content.model_dump(exclude={"options"}),
            options=[ScenarioOption(option_id=option.option_id, text=option.text) for option in content.options],
            option_feedback=result.option_feedback,
        )

    def _generate_scenario(self, request: ScenarioRequest) -> PracticeScenario:
        """Get one scenario of the requested activity type from the provider
        and validate it."""
        try:
            raw = call_provider(
                self.provider.generate_scenario,
                request,
                self.provider_timeout_seconds,
            )
            content = ScenarioContent.model_validate(raw)
            if content.activity_type != request.activity_type:
                raise ScenarioProviderError("provider returned a different activity type")
        except (ScenarioProviderError, ValidationError) as exc:
            # Log the failure type only - never career context or provider output.
            logger.warning("Scenario provider could not supply a scenario (%s)", type(exc).__name__)
            raise practice_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "SCENARIO_UNAVAILABLE",
                "A practice scenario could not be prepared. Please try again.",
            ) from None

        return PracticeScenario(
            **content.model_dump(exclude={"options"}),
            options=[ScenarioOption(option_id=option.option_id, text=option.text) for option in content.options],
            status="current",
        )
