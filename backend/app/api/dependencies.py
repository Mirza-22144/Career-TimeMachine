from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import HAS_DATABASE, SCENARIO_PROVIDER_TIMEOUT_SECONDS
from app.core.security_events import log_security_event
from app.core.tokens import is_well_formed_token
from app.providers.ai_pool_scenario_provider import AiPoolScenarioProvider
from app.providers.ml_role_prediction_provider import MLRolePredictionProvider
from app.providers.role_prediction_provider import RolePredictionProvider
from app.providers.scenario_provider import ScenarioProvider
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_practice_session_repository import (
    MemoryPracticeSessionRepository,
)
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.repositories.memory.memory_session_repository import MemorySessionRepository
from app.services.career_direction_service import CareerDirectionService
from app.services.career_journey_service import CareerJourneyService
from app.services.career_translation_service import CareerTranslationService
from app.services.catalogue_service import CatalogueService
from app.services.practice_role_service import PracticeRoleService
from app.services.practice_session_service import PracticeSessionService
from app.services.profile_service import ProfileService
from app.services.role_prediction_service import RolePredictionService
from app.services.scenario_response_service import ScenarioResponseService
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


def get_session_service() -> SessionService:
    """Build the service with the shared repo. Routes ask for this."""
    return SessionService(_session_repository)


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
    """Build role-prediction service with shared repositories and the
    trained-model provider; tests override this to fake predictions."""
    return RolePredictionService(_profile_repository, _catalogue_repository, _role_prediction_provider)


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


def get_scenario_response_service(
    practice_sessions: PracticeSessionService = Depends(get_practice_session_service),
) -> ScenarioResponseService:
    """Build response service on top of the practice-session service."""
    return ScenarioResponseService(practice_sessions)
