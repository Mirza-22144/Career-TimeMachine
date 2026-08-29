from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_current_session, get_profile_service
from app.repositories.interfaces.session_repository import AnonSession
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def read_profile(
    session: AnonSession = Depends(get_current_session),
    service: ProfileService = Depends(get_profile_service),
):
    """Return the current session's profile, creating an empty draft if needed."""
    return service.get_or_create(session.token)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    update: ProfileUpdate,
    session: AnonSession = Depends(get_current_session),
    service: ProfileService = Depends(get_profile_service),
):
    """Save partial profile data for the current anonymous session."""
    return service.update_profile(session.token, update)


@router.post("/confirm", response_model=ProfileResponse)
def confirm_profile(
    session: AnonSession = Depends(get_current_session),
    service: ProfileService = Depends(get_profile_service),
):
    """Mark the current profile as confirmed if it is complete."""
    return service.confirm_profile(session.token)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    session: AnonSession = Depends(get_current_session),
    service: ProfileService = Depends(get_profile_service),
):
    """Delete the current session's profile and return an empty 204 response."""
    service.delete_profile(session.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
