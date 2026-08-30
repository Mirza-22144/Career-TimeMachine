from abc import ABC, abstractmethod
from dataclasses import dataclass




@dataclass
class CatalogueItem:
    """One selectable option. id = stable code stored in the profile;
    label = human text the frontend shows. in_demand/hot_technology are
    O*NET signals used only for skills (see DATA_HANDOVER.md 4.2); they
    default False for every other catalogue kind."""
    id: str
    label: str
    in_demand: bool = False
    hot_technology: bool = False


class CatalogueRepository(ABC):
    """Supplies the curated option lists. In-memory now, PostgreSQL later."""

    @abstractmethod
    def get_items(self, kind: str) -> list[CatalogueItem]:
        """Return the list for a kind (e.g. 'roles'); [] if kind unknown."""
        raise NotImplementedError

    @abstractmethod
    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        """Skills relevant to a previous role (DATA_HANDOVER.md 4.1/5.2),
        ordered in_demand desc, hot_technology desc, label. Falls back to
        the full skills list when role_id is None or has no mapping."""
        raise NotImplementedError
