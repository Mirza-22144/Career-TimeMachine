from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import get_current_session, get_practice_session_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.practice_session import (
    PracticePlanResponse,
    PracticeSessionCreate,
    PracticeSessionResponse,
    RecentActivityResponse,
)
from app.services.practice_session_service import PracticeSessionService

router = APIRouter(prefix="/practice-sessions", tags=["practice-sessions"])

SessionId = Path(min_length=1, max_length=64)


@router.post("", response_model=PracticeSessionResponse, status_code=status.HTTP_201_CREATED)
def start_practice_session(
    settings: PracticeSessionCreate,
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """Start workplace practice using the saved role and the chosen settings."""
    practice = service.start_session(session.token_hash, settings)
    return PracticeSessionResponse.model_validate(practice)


@router.get("/current", response_model=PracticeSessionResponse)
def read_current_practice_session(
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """Return the active practice session so the user can resume it."""
    return PracticeSessionResponse.model_validate(service.get_current_session(session.token_hash))


@router.get("/remaining", response_model=dict[str, dict[str, int]])
def read_remaining_questions(
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """AC 4.3.5 / 4.5.4: how many questions are still new to her for her
    practice role, per kind of activity and difficulty - so the screens can
    unlock the next activity, or offer the "activities run out" choices,
    without starting anything."""
    return service.remaining_by_difficulty(session.token_hash)


@router.get("/plan", response_model=PracticePlanResponse)
def read_practice_plan(
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """What she can practise next for her practice role: what is left, the
    one activity unlocked at each level, and the level she last used."""
    return PracticePlanResponse.model_validate(service.practice_plan(session.token_hash), from_attributes=True)


@router.get("/recent-activities", response_model=list[RecentActivityResponse])
def read_recent_activities(
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """AC 3.4.1: completed activities for the dashboard, newest first.
    Registered before /{session_id} so "recent-activities" is never
    swallowed as a session id."""
    return [RecentActivityResponse.model_validate(a) for a in service.list_recent_activities(session.token_hash)]


@router.get("/{session_id}", response_model=PracticeSessionResponse)
def read_practice_session(
    session_id: str = SessionId,
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """Return one of the current user's practice sessions."""
    return PracticeSessionResponse.model_validate(service.get_session(session.token_hash, session_id))


@router.post("/{session_id}/complete", response_model=PracticeSessionResponse)
def complete_practice_session(
    session_id: str = SessionId,
    session: AnonSession = Depends(get_current_session),
    service: PracticeSessionService = Depends(get_practice_session_service),
):
    """Finish a practice session (AC 4.5.3)."""
    practice = service.complete_session(session.token_hash, session_id)
    return PracticeSessionResponse.model_validate(practice)
