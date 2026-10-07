from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session, get_role_prediction_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.predicted_roles import PredictedRolesResponse
from app.services.role_prediction_service import RolePredictionService

router = APIRouter(prefix="/predicted-roles", tags=["predicted-roles"])


@router.get("", response_model=PredictedRolesResponse)
def read_predicted_roles(
    session: AnonSession = Depends(get_current_session),
    service: RolePredictionService = Depends(get_role_prediction_service),
):
    """BE 3.4: two AI-predicted future roles for the session's previous role
    and skills, each with real Australian hiring-demand data where
    available. Empty list if no prediction is available yet. Additive to
    the existing GET /predicted-role (singular) - that endpoint is
    unchanged and still live for the current frontend."""
    return service.predict_two_for_session(session.token_hash)
