from fastapi import APIRouter, Depends

from app.api.dependencies import get_career_direction_service, get_current_session
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.career_direction import (
    CareerDirectionResponse,
    CareerDirectionUpdate,
)
from app.services.career_direction_service import CareerDirectionService

router = APIRouter(prefix="/career-direction", tags=["career-direction"])


@router.get("", response_model=CareerDirectionResponse)
def read_career_direction(
    session: AnonSession = Depends(get_current_session),
    service: CareerDirectionService = Depends(get_career_direction_service),
):
    """Return the current session's saved direction choices."""
    return service.get_for_session(session.token)


@router.patch("", response_model=CareerDirectionResponse)
def update_career_direction(
    update: CareerDirectionUpdate,
    session: AnonSession = Depends(get_current_session),
    service: CareerDirectionService = Depends(get_career_direction_service),
):
    """Save direction choices for later use without generating scenarios."""
    return service.update_for_session(session.token, update)
