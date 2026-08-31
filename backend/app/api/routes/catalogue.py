from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_catalogue_service
from app.schemas.catalogue import CatalogueItemResponse
from app.services.catalogue_service import CatalogueService

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


@router.get("/roles", response_model=list[CatalogueItemResponse])
def get_roles(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the list of previous-role options for step 1 of the wizard."""
    return service.get("roles")


@router.get("/experience-options", response_model=list[CatalogueItemResponse])
def get_experience_options(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the years-of-experience options for step 1 of the wizard."""
    return service.get("experience-options")


@router.get("/skills", response_model=list[CatalogueItemResponse])
def get_skills(
    role_id: str | None = Query(default=None),
    service: CatalogueService = Depends(get_catalogue_service),
):
    """Return skill options for step 2 of the wizard. Pass role_id to get
    only the skills linked to that role; omit it for the full list."""
    return service.get_skills(role_id)


@router.get("/responsibilities", response_model=list[CatalogueItemResponse])
def get_responsibilities(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the responsibility options for step 2 of the wizard."""
    return service.get("responsibilities")


@router.get("/break-reasons", response_model=list[CatalogueItemResponse])
def get_break_reasons(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the career-break reason options for step 3 of the wizard."""
    return service.get("break-reasons")


@router.get("/return-statuses", response_model=list[CatalogueItemResponse])
def get_return_statuses(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the return-readiness options for the career-direction step."""
    return service.get("return-statuses")


@router.get("/career-areas", response_model=list[CatalogueItemResponse])
def get_career_areas(service: CatalogueService = Depends(get_catalogue_service)):
    """Return the career-area options for the career-direction step."""
    return service.get("career-areas")
