"""Job-description extraction provider backed by the AI team's local GLiNER
model (gliner-community/gliner_small-v2.5) plus catalogue matching and
deterministic rules - see backend/ai/job_description_extraction/ for the
full handover (evaluation evidence, robustness tests, MODEL_DEPLOYMENT.md).

Heavy imports (gliner, torch, transformers) happen inside __init__, not at
module level, so this module can be imported even where they are not
installed - only actually constructing GlinerJobDescriptionExtractionProvider
needs them. dependencies.py relies on this: it decides whether to build one
of these based on HAS_JOB_DESCRIPTION_MODEL, without ever needing the heavy
packages just to start the app or run the test suite.
"""

from pathlib import Path
from typing import Any

from app.providers.job_description_extraction_provider import (
    JobDescriptionExtractionProvider,
    JobDescriptionExtractionProviderError,
    JobDescriptionExtractionRequest,
)

# The runtime module and skill catalogue live under app/ml/ (not backend/ai/)
# because the Dockerfile only copies app/ into the deployed image - the same
# lesson role prediction already hit (see app/ml/career_role_predictor.py).
_CATALOGUE_PATH = (
    Path(__file__).resolve().parent.parent / "ml" / "job_description_extraction" / "skill_catalogue.json"
)


class GlinerJobDescriptionExtractionProvider(JobDescriptionExtractionProvider):
    """Serves the AI team's real local GLiNER-based extractor.

    Loads the model once when constructed (dependencies.py builds one
    instance at import time, not per request - loading a ~1.3GB model per
    request would be unusable), with local_files_only so no network call to
    Hugging Face happens at runtime (MODEL_DEPLOYMENT.md). The returned
    extractor's own extract() is already the AI team's secured entry point
    (instruction-like content stripped, output contract-validated) - see
    job_description_extractor.py's module-level monkeypatch of
    TunedJobDescriptionExtractor.extract to secure_extract.
    """

    def __init__(self, model_dir: Path) -> None:
        # Imported here, not at module level - see the module docstring.
        from app.ml.job_description_extraction.job_description_extractor import load_extractor

        self._extractor = load_extractor(str(model_dir), str(_CATALOGUE_PATH))

    def extract(self, request: JobDescriptionExtractionRequest) -> dict[str, Any]:
        try:
            return self._extractor.extract(request.raw_text)
        except Exception as exc:
            # The extractor raises ValueError for contract/security
            # rejections; treat any failure the same way, matching
            # ScenarioProvider's "every failure becomes a provider error"
            # contract.
            raise JobDescriptionExtractionProviderError("job description extraction failed") from exc
