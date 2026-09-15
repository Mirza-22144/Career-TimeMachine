from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import get_current_session, get_scenario_response_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.practice_session import PracticeProgressResponse
from app.schemas.scenario_response import ScenarioResponseCreate, ScenarioSubmissionResponse
from app.services.scenario_response_service import ScenarioResponseService

router = APIRouter(prefix="/practice-sessions", tags=["practice-responses"])

SessionId = Path(min_length=1, max_length=64)
ScenarioId = Path(min_length=1, max_length=64)


@router.post(
    "/{session_id}/scenarios/{scenario_id}/response",
    response_model=ScenarioSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_scenario_response(
    submission: ScenarioResponseCreate,
    session_id: str = SessionId,
    scenario_id: str = ScenarioId,
    session: AnonSession = Depends(get_current_session),
    service: ScenarioResponseService = Depends(get_scenario_response_service),
):
    """Save a written response and return reflective feedback (AC 4.4.2, 4.5.1)."""
    result = service.submit_response(session.token_hash, session_id, scenario_id, submission)
    return ScenarioSubmissionResponse.model_validate(result)


@router.get("/{session_id}/progress", response_model=PracticeProgressResponse)
def read_practice_progress(
    session_id: str = SessionId,
    session: AnonSession = Depends(get_current_session),
    service: ScenarioResponseService = Depends(get_scenario_response_service),
):
    """Return completed and current scenario status for a practice session."""
    return PracticeProgressResponse.model_validate(service.get_progress(session.token_hash, session_id))
