"""Fallback used when the real GLiNER model is not present on disk (a fresh
checkout, a local dev machine that hasn't pulled the ~1.3GB model, or any
environment HAS_JOB_DESCRIPTION_MODEL is false for).

There is no sensible fake-but-useful content to return here, unlike the
in-memory repositories or the curated scenario provider - fabricating
extracted skills/responsibilities would actively mislead whoever reads them.
Always fails cleanly instead, matching how a genuinely down provider behaves.
"""

from typing import Any

from app.providers.job_description_extraction_provider import (
    JobDescriptionExtractionProvider,
    JobDescriptionExtractionProviderError,
    JobDescriptionExtractionRequest,
)


class UnavailableJobDescriptionExtractionProvider(JobDescriptionExtractionProvider):
    """Always raises - the model this needs is not available right now."""

    def extract(self, request: JobDescriptionExtractionRequest) -> dict[str, Any]:
        raise JobDescriptionExtractionProviderError(
            "job description extraction model is not available in this environment"
        )
