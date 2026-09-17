from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session, get_role_prediction_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.predicted_role import PredictedRoleResponse
from app.services.role_prediction_service import RolePredictionService

router = APIRouter(prefix="/predicted-role", tags=["predicted-role"])


@router.get("", response_model=PredictedRoleResponse)
def read_predicted_role(
    session: AnonSession = Depends(get_current_session),
    service: RolePredictionService = Depends(get_role_prediction_service),
):
    """Return the AI-predicted future role for the session's previous role
    and skills (all null if no prediction is available yet)."""
    return service.predict_for_session(session.token_hash)
