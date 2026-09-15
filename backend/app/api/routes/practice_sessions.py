from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import get_current_session, get_practice_session_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.practice_session import PracticeSessionCreate, PracticeSessionResponse
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
