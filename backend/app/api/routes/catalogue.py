
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_catalogue_service
from app.schemas.catalogue import CatalogueItemResponse
from app.services.catalogue_service import CatalogueService

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

# Every endpoint returns a list of {id, label}. Thin: just call the service.
@router.get("/roles", response_model=list[CatalogueItemResponse])
def get_roles(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("roles")

@router.get("/experience-options", response_model=list[CatalogueItemResponse])
def get_experience_options(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("experience-options")

# role_id filters to skills relevant to that previous role (DATA_HANDOVER.md
# 4.1/5.2); omitted, it falls back to the full flat list.
@router.get("/skills", response_model=list[CatalogueItemResponse])
def get_skills(
    role_id: str | None = Query(default=None),
    service: CatalogueService = Depends(get_catalogue_service),
):
    return service.get_skills(role_id)

@router.get("/responsibilities", response_model=list[CatalogueItemResponse])
def get_responsibilities(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("responsibilities")

@router.get("/break-reasons", response_model=list[CatalogueItemResponse])
def get_break_reasons(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("break-reasons")

@router.get("/return-statuses", response_model=list[CatalogueItemResponse])
def get_return_statuses(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("return-statuses")

@router.get("/career-areas", response_model=list[CatalogueItemResponse])
def get_career_areas(service: CatalogueService = Depends(get_catalogue_service)):
    return service.get("career-areas")