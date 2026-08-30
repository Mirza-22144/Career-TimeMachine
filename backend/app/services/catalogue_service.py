from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)


class CatalogueService:
    def __init__(self, catalogue: CatalogueRepository) -> None:
        self.catalogue = catalogue          # depends on the interface

    def get(self, kind: str) -> list[CatalogueItem]:
        return self.catalogue.get_items(kind)

    def get_skills(self, role_id: str | None) -> list[CatalogueItem]:
        return self.catalogue.get_skills_for_role(role_id)

    