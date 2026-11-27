from fastapi import APIRouter, Depends

from app.api.dependencies import get_career_journey_service, get_current_session
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.career_journey import CareerJourneyResponse
from app.services.career_journey_service import CareerJourneyService

router = APIRouter(prefix="/career-journey", tags=["career-journey"])


@router.get("", response_model=CareerJourneyResponse)
def read_career_journey(
    session: AnonSession = Depends(get_current_session),
    service: CareerJourneyService = Depends(get_career_journey_service),
):
    """Return the confirmed profile as a structured career journey."""
    return service.build_for_session(session.token)
