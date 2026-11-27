from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)


class CatalogueService:
    """Fetches option lists like roles and skills. Used by the catalogue
    routes and by other services that need to look up a label from an id."""

    def __init__(self, catalogue: CatalogueRepository) -> None:
        self.catalogue = catalogue          # depends on the interface

    def get(self, kind: str) -> list[CatalogueItem]:
        """Return the option list for a kind (e.g. 'roles')."""
        return self.catalogue.get_items(kind)

    def get_skills(self, role_id: str | None) -> list[CatalogueItem]:
        """Return the skills that go with a role, or the full list if no
        role is given."""
        return self.catalogue.get_skills_for_role(role_id)

    