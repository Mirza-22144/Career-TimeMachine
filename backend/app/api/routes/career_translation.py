from fastapi import APIRouter, Depends

from app.api.dependencies import get_career_translation_service, get_current_session
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.career_translation import SkillRelevanceMapResponse
from app.services.career_translation_service import CareerTranslationService

router = APIRouter(prefix="/career-translation", tags=["career-translation"])


@router.get("", response_model=SkillRelevanceMapResponse)
def read_career_translation(
    session: AnonSession = Depends(get_current_session),
    service: CareerTranslationService = Depends(get_career_translation_service),
):
    """Return the Skill Relevance Map for step 4 of the wizard: skills the
    user brings back vs current in-demand skills ('New Horizons') for her
    selected role."""
    return service.build_for_session(session.token)
