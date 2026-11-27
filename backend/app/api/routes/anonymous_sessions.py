from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_session, get_session_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.anonymous_session import AnonSessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/anonymous-sessions", tags=["anonymous-sessions"])


@router.post("", response_model=AnonSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(service: SessionService = Depends(get_session_service)):
    """Screen 1: start a journey. Returns a token the client stores and
    sends back as X-Session-Token on later requests."""
    return service.start_session()


@router.get("/current", response_model=AnonSessionResponse)
def read_current_session(session: AnonSession = Depends(get_current_session)):
    """Return the session for the X-Session-Token header (401 if missing/invalid)."""
    return session

