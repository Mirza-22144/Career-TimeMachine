from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session, get_roadmap_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.roadmap import RoadmapResponse
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.get("", response_model=RoadmapResponse)
def read_roadmap(
    session: AnonSession = Depends(get_current_session),
    service: RoadmapService = Depends(get_roadmap_service),
):
    """Your Roadmap: the previous role and up to two suggested roles, each
    with Skills You Bring Back, Skills You Could Explore and market data."""
    return service.build_for_session(session.token_hash)
