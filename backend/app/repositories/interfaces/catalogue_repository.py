from abc import ABC, abstractmethod
from dataclasses import dataclass




@dataclass
class CatalogueItem:
    """One selectable option. id = stable code stored in the profile;
    label = human text the frontend shows."""
    id: str
    label: str


class CatalogueRepository(ABC):
    """Supplies the curated option lists. In-memory now, PostgreSQL later."""

    @abstractmethod
    def get_items(self, kind: str) -> list[CatalogueItem]:
        """Return the list for a kind (e.g. 'roles'); [] if kind unknown."""
        raise NotImplementedError

    