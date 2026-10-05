from fastapi import APIRouter, Depends, Path, Request, status

from app.api.dependencies import get_current_session, get_job_description_service
from app.core.rate_limit import JOB_DESCRIPTION_SUBMISSION_LIMIT, limiter
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.services.job_description_service import JobDescriptionService

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])

JobDescriptionId = Path(min_length=1, max_length=64)


@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(JOB_DESCRIPTION_SUBMISSION_LIMIT)
def create_job_description(
    request: Request,
    body: JobDescriptionCreate,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionService = Depends(get_job_description_service),
):
    """Extract structured requirements from a pasted job description
    (Path 1, Step 3)."""
    result = service.extract_and_save(session.token_hash, body.raw_text)
    return JobDescriptionResponse.model_validate(result)


@router.get("", response_model=list[JobDescriptionResponse])
def list_job_descriptions(
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionService = Depends(get_job_description_service),
):
    """Every job description the user has pasted, newest first."""
    return [JobDescriptionResponse.model_validate(jd) for jd in service.list_for_owner(session.token_hash)]


@router.get("/{job_description_id}", response_model=JobDescriptionResponse)
def read_job_description(
    job_description_id: str = JobDescriptionId,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionService = Depends(get_job_description_service),
):
    """One of the user's job descriptions."""
    result = service.get_for_owner(session.token_hash, job_description_id)
    return JobDescriptionResponse.model_validate(result)
