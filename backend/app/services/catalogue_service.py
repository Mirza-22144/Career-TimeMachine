from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)


class CatalogueService:
    def __init__(self, catalogue: CatalogueRepository) -> None:
        self.catalogue = catalogue          # depends on the interface

    def get(self, kind: str) -> list[CatalogueItem]:
        return self.catalogue.get_items(kind)

    