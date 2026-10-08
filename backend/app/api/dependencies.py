import logging
import threading

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import (
    HAS_DATABASE,
    HAS_JOB_DESCRIPTION_MODEL,
    JOB_DESCRIPTION_MODEL_DIR,
    JOB_DESCRIPTION_PROVIDER_TIMEOUT_SECONDS,
    SCENARIO_PROVIDER_TIMEOUT_SECONDS,
)
from app.core.security_events import log_security_event
from app.core.tokens import is_well_formed_token
from app.providers.ai_pool_scenario_provider import AiPoolScenarioProvider
from app.providers.job_description_extraction_provider import JobDescriptionExtractionProvider
from app.providers.ml_role_prediction_provider import MLRolePredictionProvider
from app.providers.ml_two_role_prediction_provider import MLTwoRolePredictionProvider
from app.providers.role_prediction_provider import RolePredictionProvider
from app.providers.scenario_provider import ScenarioProvider
from app.providers.two_role_prediction_provider import TwoRolePredictionProvider
from app.providers.unavailable_job_description_extraction_provider import (
    UnavailableJobDescriptionExtractionProvider,
)
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.job_description_repository import JobDescriptionRepository
from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.interfaces.vacancy_repository import VacancyRepository
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_job_description_repository import (
    MemoryJobDescriptionRepository,
)
from app.repositories.memory.memory_practice_session_repository import (
    MemoryPracticeSessionRepository,
)
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.repositories.memory.memory_session_repository import MemorySessionRepository
from app.repositories.memory.memory_vacancy_repository import MemoryVacancyRepository
from app.services.career_direction_service import CareerDirectionService
from app.services.career_journey_service import CareerJourneyService
from app.services.career_translation_service import CareerTranslationService
from app.services.catalogue_service import CatalogueService
from app.services.job_description_service import JobDescriptionService
from app.services.practice_role_service import PracticeRoleService
from app.services.practice_session_service import PracticeSessionService
from app.services.profile_service import ProfileService
from app.services.role_prediction_service import RolePredictionService
from app.services.scenario_response_service import ScenarioResponseService
from app.services.job_description_comparison_service import JobDescriptionComparisonService
from app.services.roadmap_service import RoadmapService
from app.services.session_service import SessionService

# Iteration 2 serves single-selection multiple-choice activities.
# "written_response" is still supported for later iterations.
PRACTICE_ACTIVITY_TYPE = "multiple_choice"

# Sessions, profiles and practice sessions use the real database once the
# DB_* env vars are set; falls back to the in-memory store otherwise (e.g. a
# fresh checkout with no .env yet).
if HAS_DATABASE:
    from app.repositories.postgres.postgres_practice_session_repository import (
        PostgresPracticeSessionRepository,
    )
    from app.repositories.postgres.postgres_profile_repository import (
        PostgresProfileRepository,
    )
    from app.repositories.postgres.postgres_session_repository import (
        PostgresSessionRepository,
    )

    _session_repository = PostgresSessionRepository()
    _profile_repository = PostgresProfileRepository()
    _practice_session_repository = PostgresPracticeSessionRepository()
else:
    _session_repository = MemorySessionRepository()
    _profile_repository = MemoryProfileRepository()
    _practice_session_repository = MemoryPracticeSessionRepository()

# Job descriptions use the real database once the DB_* env vars are set,
# same as everything else above - independent of whether the extraction
# model itself is available.
_job_description_repository: JobDescriptionRepository
if HAS_DATABASE:
    from app.repositories.postgres.postgres_job_description_repository import (
        PostgresJobDescriptionRepository,
    )

    _job_description_repository = PostgresJobDescriptionRepository()
else:
    _job_description_repository = MemoryJobDescriptionRepository()

# The real GLiNER-based extractor (app/ml/job_description_extraction/,
# handed over by the AI team - see AI 3.1) loads a ~1.3GB model and, on a
# machine that has never loaded it before, needs one-time network access
# to resolve its base encoder's config (microsoft/deberta-v3-small) into
# the local Hugging Face cache - confirmed directly while wiring this up.
# Built lazily, on first actual use, not at import time: a fresh checkout,
# a test run, or any transient load failure must never take down the whole
# app just because this one feature's model had a problem. Falls back to a
# provider that cleanly fails every request if construction fails for any
# reason, same "unavailable, not faked" principle as a down external
# service - logged loudly, since an unexpected fallback here is worth
# knowing about.
_job_description_extraction_provider: JobDescriptionExtractionProvider | None = None
# Guards building the provider above - model loading takes several seconds,
# a real window for concurrent first requests to race on FastAPI's thread
# pool. Matches the care already taken with the Postgres connection pools
# elsewhere in this backend, after a genuine thread-safety bug there.
_job_description_extraction_provider_lock = threading.Lock()


def _build_job_description_extraction_provider() -> JobDescriptionExtractionProvider:
    if not HAS_JOB_DESCRIPTION_MODEL:
        return UnavailableJobDescriptionExtractionProvider()
    try:
        from app.providers.gliner_job_description_extraction_provider import (
            GlinerJobDescriptionExtractionProvider,
        )

        return GlinerJobDescriptionExtractionProvider(JOB_DESCRIPTION_MODEL_DIR)
    except Exception:
        logging.getLogger(__name__).exception(
            "Job-description extraction model failed to load - falling back to unavailable"
        )
        return UnavailableJobDescriptionExtractionProvider()

# Real AI-generated scenarios (27 roles x 3 difficulties, Version 2 -
# app/data/reflective_mcq_scenario_pool_v2.json) until the AI team exposes
# their model as a live external API - this is a drop-in replacement for
# that call, same ScenarioProvider interface, so swapping in the real API
# later only touches this one provider class, not any route/service code.
_scenario_provider: ScenarioProvider = AiPoolScenarioProvider()

# Real trained career-role classifier (see app/ml/career_role_predictor.py),
# runs in-process - no external API or key involved (see role_prediction
# handover, app/../ai/role_prediction/README.md).
_role_prediction_provider: RolePredictionProvider = MLRolePredictionProvider()

# BE 3.4: the AI team's Version 2 two-role classifier (AI 3.2, see
# app/ml/career_role_predictor_v2.py) - a small joblib bundle like V1, no
# heavy deps, so loaded eagerly at import time same as the V1 provider
# above (unlike the job-description model, which is a different scale
# entirely and is loaded lazily - see get_job_description_extraction_provider).
_two_role_prediction_provider: TwoRolePredictionProvider = MLTwoRolePredictionProvider()

# Roles and skills use the real database once the DB_* env vars are set;
# falls back to the placeholder list otherwise.
_catalogue_repository: CatalogueRepository
if HAS_DATABASE:
    from app.repositories.postgres.postgres_catalogue_repository import (
        PostgresCatalogueRepository,
    )

    _catalogue_repository = PostgresCatalogueRepository()
else:
    _catalogue_repository = MemoryCatalogueRepository()

# Real Australian hiring-demand data (DB 3.1 - role_anzsco_map +
# vacancy_monthly, read-only reference data maintained by the data team's
# pipeline) once the DB_* env vars are set; empty otherwise, same pattern
# as every other repository here.
_vacancy_repository: VacancyRepository
if HAS_DATABASE:
    from app.repositories.postgres.postgres_vacancy_repository import (
        PostgresVacancyRepository,
    )

    _vacancy_repository = PostgresVacancyRepository()
else:
    _vacancy_repository = MemoryVacancyRepository()


def get_session_service() -> SessionService:
    """Build the service with the shared repos. Routes ask for this."""
    return SessionService(_session_repository, _profile_repository, _job_description_repository)


def get_current_session(
    request: Request,
    # FastAPI maps this param to the "X-Session-Token" request header.
    x_session_token: str | None = Header(default=None),
    service: SessionService = Depends(get_session_service),
) -> AnonSession:
    """Turn the header token into a real session, or reject the request.
    Used by every protected route to identify who is calling.

    Every rejection is logged as a security event. Only the reason is
    logged, never the presented token (it may be a mistyped real token or
    something else the user pasted). The client still gets the same
    response for malformed and unknown tokens."""
    if x_session_token is None:
        log_security_event("auth_failed", request, reason="missing_token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing session token")
    session = service.get_current(x_session_token)
    if session is None:
        reason = "unknown_token" if is_well_formed_token(x_session_token) else "malformed_token"
        log_security_event("auth_failed", request, reason=reason)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session token")
    return session


def get_catalogue_service() -> CatalogueService:
    """Build catalogue service around the shared development-only repo."""
    return CatalogueService(_catalogue_repository)


def get_profile_service() -> ProfileService:
    """Build profile service with shared profile and catalogue repositories."""
    return ProfileService(_profile_repository, _catalogue_repository)


def get_career_journey_service() -> CareerJourneyService:
    """Build journey service with shared profile and catalogue repositories."""
    return CareerJourneyService(_profile_repository, _catalogue_repository)


def get_career_translation_service() -> CareerTranslationService:
    """Build translation service with shared profile and catalogue repositories."""
    return CareerTranslationService(_profile_repository, _catalogue_repository)


def get_career_direction_service() -> CareerDirectionService:
    """Build direction service with shared profile and catalogue repositories."""
    return CareerDirectionService(_profile_repository, _catalogue_repository)


def get_practice_role_service() -> PracticeRoleService:
    """Build practice-role service with shared profile and catalogue repositories."""
    return PracticeRoleService(_profile_repository, _catalogue_repository)


def get_role_prediction_service() -> RolePredictionService:
    """Build role-prediction service with shared repositories and both the
    V1 (single-role) and V2 (two-role, BE 3.4) trained-model providers;
    tests override this to fake predictions."""
    return RolePredictionService(
        _profile_repository,
        _catalogue_repository,
        _role_prediction_provider,
        _two_role_prediction_provider,
        _vacancy_repository,
    )


def get_scenario_provider() -> ScenarioProvider:
    """Return the workplace-scenario provider. The AI provider plugs in here;
    tests override this to simulate provider failures."""
    return _scenario_provider


def get_practice_activity_type() -> str:
    """Return the activity type new practice scenarios use. Tests override
    this to exercise written responses."""
    return PRACTICE_ACTIVITY_TYPE


def get_practice_session_service(
    provider: ScenarioProvider = Depends(get_scenario_provider),
    activity_type: str = Depends(get_practice_activity_type),
) -> PracticeSessionService:
    """Build practice-session service with shared repositories and the provider."""
    return PracticeSessionService(
        _practice_session_repository,
        get_practice_role_service(),
        provider,
        SCENARIO_PROVIDER_TIMEOUT_SECONDS,
        activity_type,
    )


def get_job_description_comparison_service(
    predictions: RolePredictionService = Depends(get_role_prediction_service),
) -> JobDescriptionComparisonService:
    """Build the profile-vs-job comparison service with shared repositories."""
    return JobDescriptionComparisonService(
        _job_description_repository,
        _profile_repository,
        _catalogue_repository,
        predictions,
    )


def get_roadmap_service(
    predictions: RolePredictionService = Depends(get_role_prediction_service),
) -> RoadmapService:
    """Build the roadmap service. Takes the prediction service as a
    dependency so tests that fake predictions fake the roadmap's too."""
    return RoadmapService(
        _profile_repository,
        _catalogue_repository,
        predictions,
        get_practice_role_service(),
        _practice_session_repository,
    )


def get_scenario_response_service(
    practice_sessions: PracticeSessionService = Depends(get_practice_session_service),
) -> ScenarioResponseService:
    """Build response service on top of the practice-session service."""
    return ScenarioResponseService(practice_sessions)


def get_job_description_extraction_provider() -> JobDescriptionExtractionProvider:
    """Return the job-description extraction provider, building it on first
    use and caching it after (not at import time - see the module-level
    comment above). Real GLiNER model if present and loads successfully,
    otherwise a provider that cleanly fails; tests override this to
    simulate both a working extractor and provider failures."""
    global _job_description_extraction_provider
    if _job_description_extraction_provider is None:
        with _job_description_extraction_provider_lock:
            if _job_description_extraction_provider is None:
                _job_description_extraction_provider = _build_job_description_extraction_provider()
    return _job_description_extraction_provider


def get_job_description_service(
    provider: JobDescriptionExtractionProvider = Depends(get_job_description_extraction_provider),
) -> JobDescriptionService:
    """Build job-description service with the shared repository and the
    extraction provider."""
    return JobDescriptionService(
        _job_description_repository, provider, JOB_DESCRIPTION_PROVIDER_TIMEOUT_SECONDS
    )
