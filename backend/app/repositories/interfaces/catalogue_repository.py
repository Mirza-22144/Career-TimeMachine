from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CatalogueItem:
    """One selectable option. id is the stable code saved on the profile;
    label is the text shown to the user. in_demand/hot_technology are only
    used for skills and stay False for every other kind."""
    id: str
    label: str
    in_demand: bool = False
    hot_technology: bool = False


class CatalogueRepository(ABC):
    """Supplies the option lists (roles, skills, break reasons, and so on).
    In-memory now, real database later - services depend on this interface
    so the storage behind it can change without touching them."""

    @abstractmethod
    def get_items(self, kind: str) -> list[CatalogueItem]:
        """Return the list for a kind (e.g. 'roles'); [] if kind is unknown.
        Used by the catalogue endpoints and by other services that need to
        look up a label from an id."""
        raise NotImplementedError

    @abstractmethod
    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        """Skills that go with a previous role, sorted in_demand first, then
        hot_technology, then label. Falls back to the full skills list when
        role_id is missing or has no matching skills. Used by the skills
        catalogue endpoint and the skill relevance comparison."""
        raise NotImplementedError
