from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session, get_practice_role_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.practice_role import PracticeRoleResponse, PracticeRoleUpdate
from app.services.practice_role_service import PracticeRoleService

router = APIRouter(prefix="/practice-role", tags=["practice-role"])


@router.get("", response_model=PracticeRoleResponse)
def read_practice_role(
    session: AnonSession = Depends(get_current_session),
    service: PracticeRoleService = Depends(get_practice_role_service),
):
    """Return the role saved for workplace practice (all null if none)."""
    return service.get_for_session(session.token_hash)


@router.put("", response_model=PracticeRoleResponse)
def save_practice_role(
    selection: PracticeRoleUpdate,
    session: AnonSession = Depends(get_current_session),
    service: PracticeRoleService = Depends(get_practice_role_service),
):
    """Save the previous or predicted role chosen on Your Direction."""
    return service.select_for_session(session.token_hash, selection)
