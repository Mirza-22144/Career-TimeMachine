from fastapi import APIRouter, Depends

from app.api.dependencies import get_career_translation_service, get_current_session
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.career_translation import SkillTranslationResponse
from app.services.career_translation_service import CareerTranslationService

router = APIRouter(prefix="/career-translation", tags=["career-translation"])


@router.get("", response_model=list[SkillTranslationResponse])
def read_career_translation(
    session: AnonSession = Depends(get_current_session),
    service: CareerTranslationService = Depends(get_career_translation_service),
):
    """Return deterministic area connections for all selected catalogue skills."""
    return service.build_all_for_session(session.token)


@router.get("/{skill_id}", response_model=SkillTranslationResponse)
def read_skill_translation(
    skill_id: str,
    session: AnonSession = Depends(get_current_session),
    service: CareerTranslationService = Depends(get_career_translation_service),
):
    """Return deterministic area connections for one selected catalogue skill."""
    return service.build_one_for_session(session.token, skill_id)
