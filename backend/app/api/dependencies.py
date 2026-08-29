from fastapi import Depends, Header, HTTPException, status

from app.repositories.interfaces.session_repository import AnonSession
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository
from app.repositories.memory.memory_profile_repository import MemoryProfileRepository
from app.repositories.memory.memory_session_repository import MemorySessionRepository
from app.services.career_journey_service import CareerJourneyService
from app.services.catalogue_service import CatalogueService
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService

# ONE shared store for the whole app run, so sessions persist between requests.
# (Dev only. After the DB handover this line becomes the Postgres repo.)
_session_repository = MemorySessionRepository()
_catalogue_repository = MemoryCatalogueRepository()
_profile_repository = MemoryProfileRepository()


def get_session_service() -> SessionService:
    """Build the service with the shared repo. Routes ask for this."""
    return SessionService(_session_repository)


def get_current_session(
    # FastAPI maps this param to the "X-Session-Token" request header.
    x_session_token: str | None = Header(default=None),
    service: SessionService = Depends(get_session_service),
) -> AnonSession:
    """Turn the header token into a real session, or reject the request.
    NOTE: error shape is unified in Phase 14; HTTPException is fine for now."""
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
