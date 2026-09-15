import logging
from dataclasses import dataclass

from fastapi import status
from pydantic import ValidationError

from app.providers.scenario_provider import (
    FeedbackContent,
    FeedbackRequest,
    ScenarioProviderError,
)
from app.repositories.interfaces.practice_session_repository import (
    PracticeProgress,
    PracticeScenario,
    PracticeSession,
    ReflectiveFeedback,
    ScenarioAttempt,
    ScenarioOption,
    SuggestedSkill,
)
from app.schemas.scenario_response import ScenarioResponseCreate
from app.services.practice_session_service import (
    PracticeSessionService,
    call_provider,
    practice_error,
    utc_now,
)

logger = logging.getLogger(__name__)

# The one answer field each activity type accepts.
EXPECTED_ANSWER_FIELD = {"multiple_choice": "selected_option_id", "written_response": "response_text"}


@dataclass
class ScenarioSubmission:
    """Result of submitting a response: the answered scenario and progress."""

    session_id: str
    scenario: PracticeScenario
    progress: PracticeProgress


class ScenarioResponseService:
    """Saves scenario responses with reflective feedback and reports progress."""

    def __init__(self, practice_sessions: PracticeSessionService) -> None:
        # Reuses the session service for ownership checks, storage and the
        # provider, so both services always see the same data.
        self.practice_sessions = practice_sessions

    def submit_response(
        self,
        owner: str,
        session_id: str,
        scenario_id: str,
        submission: ScenarioResponseCreate,
    ) -> ScenarioSubmission:
        """Store the answer to a scenario in the owner's active session and
        attach reflective feedback when the provider can supply it.

        Checks run in this order: session (404), scenario (404), session
        active (409), not already answered (409), answer field matches the
        activity type (400), selected option belongs to the scenario (400)."""
        session = self.practice_sessions.get_session(owner, session_id)
        scenario = self._find_scenario(session, scenario_id)

        if session.status != "active":
            raise practice_error(
                status.HTTP_409_CONFLICT,
                "PRACTICE_SESSION_NOT_ACTIVE",
                "Practice session is no longer active",
            )
        if scenario.response is not None:
            raise practice_error(
                status.HTTP_409_CONFLICT,
                "RESPONSE_ALREADY_SUBMITTED",
                "A response has already been submitted for this scenario",
            )
        expected_field = EXPECTED_ANSWER_FIELD[scenario.activity_type]
        if getattr(submission, expected_field) is None:
            raise practice_error(
                status.HTTP_400_BAD_REQUEST,
                "ACTIVITY_TYPE_MISMATCH",
                f"This activity expects {expected_field}",
            )

        selected_option = (
            self._find_option(scenario, submission.selected_option_id)
            if scenario.activity_type == "multiple_choice"
            else None
        )

        feedback = self._generate_feedback(session, scenario, submission, selected_option)

        now = utc_now()
        scenario.response = ScenarioAttempt(
            submitted_at=now,
            response_text=submission.response_text,
            selected_option_id=submission.selected_option_id,
        )
        scenario.feedback = feedback
        scenario.feedback_status = "available" if feedback is not None else "unavailable"
        scenario.status = "completed"
        session.updated_at = now

        saved = self.practice_sessions.sessions.save(session)
        return ScenarioSubmission(
            session_id=saved.session_id,
            scenario=self._find_scenario(saved, scenario_id),
            progress=saved.progress,
        )

    def get_progress(self, owner: str, session_id: str) -> PracticeProgress:
        """Return completed and current scenario status for the owner's session."""
        return self.practice_sessions.get_session(owner, session_id).progress

    def _find_scenario(self, session: PracticeSession, scenario_id: str) -> PracticeScenario:
        scenario = next((s for s in session.scenarios if s.scenario_id == scenario_id), None)
        if scenario is None:
            raise practice_error(
                status.HTTP_404_NOT_FOUND,
                "SCENARIO_NOT_FOUND",
                "Scenario not found in this practice session",
            )
        return scenario

    def _find_option(self, scenario: PracticeScenario, option_id: str) -> ScenarioOption:
        """Return the selected option only if it belongs to this scenario, so an
        option id from another scenario is rejected."""
        option = next((o for o in scenario.options if o.option_id == option_id), None)
        if option is None:
            raise practice_error(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_OPTION_ID",
                "selected_option_id is not an option for this scenario",
            )
        return option

    def _generate_feedback(
        self,
        session: PracticeSession,
        scenario: PracticeScenario,
        submission: ScenarioResponseCreate,
        selected_option: ScenarioOption | None,
    ) -> ReflectiveFeedback | None:
        """Ask the provider for reflective feedback. A failure is not an error
        for the user: the response is still saved and practice can continue
        (AC 4.5.1)."""
        request = FeedbackRequest(
            role_label=session.role.label,
            difficulty=session.difficulty,
            scenario_id=scenario.scenario_id,
            situation=scenario.situation,
            task=scenario.task,
            skills_used=tuple(scenario.skills_used),
            new_skill_focus=scenario.new_skill_focus,
            activity_type=scenario.activity_type,
            response_text=submission.response_text,
            selected_option_id=selected_option.option_id if selected_option else None,
            selected_option_text=selected_option.text if selected_option else None,
            option_texts=tuple(option.text for option in scenario.options),
        )
        provider = self.practice_sessions.provider
        try:
            raw = call_provider(
                provider.generate_feedback,
                request,
                self.practice_sessions.provider_timeout_seconds,
            )
            content = FeedbackContent.model_validate(raw)
        except (ScenarioProviderError, ValidationError) as exc:
            # Log the failure type only - never the response or provider output.
            logger.warning("Scenario provider could not supply feedback (%s)", type(exc).__name__)
            return None

        suggested = content.skill_to_explore
        return ReflectiveFeedback(
            what_worked_well=list(content.what_worked_well),
            areas_to_consider=list(content.areas_to_consider),
            trade_offs=list(content.trade_offs),
            skill_to_explore=SuggestedSkill(skill=suggested.skill, why_relevant=suggested.why_relevant)
            if suggested is not None
            else None,
        )
