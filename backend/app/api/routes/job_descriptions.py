from fastapi import APIRouter, Depends, Path, Request, status

from app.api.dependencies import (
    get_current_session,
    get_job_description_comparison_service,
    get_job_description_service,
)
from app.core.rate_limit import JOB_DESCRIPTION_SUBMISSION_LIMIT, limiter
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.job_description import (
    ClosestRoleChoice,
    ClosestRolesResponse,
    JobComparisonResponse,
    JobDescriptionCreate,
    JobDescriptionResponse,
)
from app.services.job_description_comparison_service import JobDescriptionComparisonService
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


@router.get("/{job_description_id}/comparison", response_model=JobComparisonResponse)
def read_job_comparison(
    job_description_id: str = JobDescriptionId,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionComparisonService = Depends(get_job_description_comparison_service),
):
    """AC 5.2.1: how the profile relates to what this job asks for."""
    return service.compare(session.token_hash, job_description_id)


@router.get("/{job_description_id}/closest-roles", response_model=ClosestRolesResponse)
def read_closest_roles(
    job_description_id: str = JobDescriptionId,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionComparisonService = Depends(get_job_description_comparison_service),
):
    """AC 5.2.2: the roles closest to this job's title."""
    return service.closest_roles(session.token_hash, job_description_id)


@router.put("/{job_description_id}/closest-role", status_code=status.HTTP_204_NO_CONTENT)
def choose_closest_role(
    body: ClosestRoleChoice,
    job_description_id: str = JobDescriptionId,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionComparisonService = Depends(get_job_description_comparison_service),
):
    """AC 5.2.2: remember which role she chose as closest to this job."""
    service.choose_closest_role(session.token_hash, job_description_id, body.role_id)


@router.delete("/{job_description_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_description(
    job_description_id: str = JobDescriptionId,
    session: AnonSession = Depends(get_current_session),
    service: JobDescriptionService = Depends(get_job_description_service),
):
    """AC 3.5.1: remove a saved job description. Completed activities are
    unaffected - this only ever touches the job_description table."""
    service.delete_for_owner(session.token_hash, job_description_id)
