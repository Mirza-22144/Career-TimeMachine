from fastapi import Depends, Header, HTTPException, status

from app.core.config import HAS_DATABASE
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.repositories.memory.memory_session_repository import MemorySessionRepository
from app.services.career_direction_service import CareerDirectionService
from app.services.career_journey_service import CareerJourneyService
from app.services.career_translation_service import CareerTranslationService
from app.services.catalogue_service import CatalogueService
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService

# ONE shared store for the whole app run, so sessions persist between requests.
# (Dev only. Session/profile stay in-memory - their tables are empty until
# the app writes to them; there's no data to migrate from yet.)
_session_repository = MemorySessionRepository()
_profile_repository = MemoryProfileRepository()

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
    # FastAPI maps this param to the "X-Session-Token" request header.
    x_session_token: str | None = Header(default=None),
    service: SessionService = Depends(get_session_service),
) -> AnonSession:
    """Turn the header token into a real session, or reject the request.
    Used by every protected route to identify who is calling."""
    if x_session_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing session token")
    session = service.get_current(x_session_token)
    if session is None:
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
