import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.providers.job_description_extraction_provider import (
    JobDescriptionExtractionContent,
    JobDescriptionExtractionProvider,
    JobDescriptionExtractionProviderError,
    JobDescriptionExtractionRequest,
)
from app.repositories.interfaces.job_description_repository import (
    ExtractedSkill,
    JobDescription,
    JobDescriptionRepository,
)

logger = logging.getLogger(__name__)

# A local NLP model has real inference latency, unlike the catalogue/role
# providers - run it on a worker thread so a slow or hung provider can be
# abandoned after a timeout instead of holding the request open, same
# pattern as practice_session_service.call_provider.
_provider_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="job-description-extraction")


def _call_provider(
    provider: JobDescriptionExtractionProvider,
    request: JobDescriptionExtractionRequest,
    timeout_seconds: float,
) -> dict[str, Any]:
    future = _provider_executor.submit(provider.extract, request)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise JobDescriptionExtractionProviderError("provider timed out") from exc
    except JobDescriptionExtractionProviderError:
        raise
    except Exception as exc:
        raise JobDescriptionExtractionProviderError("provider failed") from exc


def _job_description_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


class JobDescriptionService:
    """Extracts structured requirements from a pasted job description and
    stores the result, keyed by the owner's session token."""

    def __init__(
        self,
        repository: JobDescriptionRepository,
        provider: JobDescriptionExtractionProvider,
        provider_timeout_seconds: float = 20.0,
    ) -> None:
        # Storage and extraction both sit behind interfaces, so the
        # database and the AI model can both be swapped without changes
        # here - same shape as PracticeSessionService.
        self.repository = repository
        self.provider = provider
        self.provider_timeout_seconds = provider_timeout_seconds

    def extract_and_save(self, owner: str, raw_text: str) -> JobDescription:
        """Run extraction, validate the result, and store it. Raises a
        structured 503 if the provider fails, times out, or returns
        something that doesn't match the agreed contract - never stores
        unvalidated AI output."""
        try:
            raw_result = _call_provider(
                self.provider,
                JobDescriptionExtractionRequest(raw_text=raw_text),
                self.provider_timeout_seconds,
            )
            validated = JobDescriptionExtractionContent.model_validate(raw_result)
        except (JobDescriptionExtractionProviderError, ValidationError):
            logger.warning("Job description extraction failed", exc_info=True)
            raise _job_description_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "JOB_DESCRIPTION_EXTRACTION_UNAVAILABLE",
                "We couldn't analyse your job description. Please try again.",
            ) from None

        job_description = JobDescription(
            job_description_id=uuid.uuid4().hex,
            owner_token_hash=owner,
            raw_text=raw_text,
            extracted_skills=[
                ExtractedSkill(label=skill.label, category=skill.category) for skill in validated.skills
            ],
            extracted_responsibilities=list(validated.responsibilities),
            min_years_experience=validated.min_years_experience,
            keywords=list(validated.keywords),
            role_title_guess=validated.role_title_guess,
            created_at=datetime.now(timezone.utc),
        )
        return self.repository.add(job_description)

    def get_for_owner(self, owner: str, job_description_id: str) -> JobDescription:
        """Return one of the owner's job descriptions. 404s rather than
        leaking whether a different owner's id exists."""
        result = self.repository.get_for_owner(owner, job_description_id)
        if result is None:
            raise _job_description_error(
                status.HTTP_404_NOT_FOUND,
                "JOB_DESCRIPTION_NOT_FOUND",
                "Job description not found",
            )
        return result

    def list_for_owner(self, owner: str) -> list[JobDescription]:
        """Return every job description the owner has pasted, newest first."""
        return self.repository.list_for_owner(owner)
