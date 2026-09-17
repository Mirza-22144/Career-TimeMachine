from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_current_session,
    get_practice_role_service,
    get_role_prediction_service,
)
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.practice_role import PracticeRoleResponse, PracticeRoleUpdate
from app.schemas.role_prediction import PredictedRoleResponse
from app.services.practice_role_service import PracticeRoleService
from app.services.role_prediction_service import RolePredictionService

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


@router.get("/predicted", response_model=PredictedRoleResponse)
def read_predicted_role(
    session: AnonSession = Depends(get_current_session),
    service: RolePredictionService = Depends(get_role_prediction_service),
):
    """Predict one future role from the confirmed profile's previous role
    and skills (AI 2.3), for Your Direction to offer alongside "previous
    role". Does not save anything - PUT /practice-role with
    source="predicted" saves the result if the user picks it."""
    return service.predict_for_session(session.token_hash)
