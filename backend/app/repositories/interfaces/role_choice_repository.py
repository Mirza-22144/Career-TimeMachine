from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoleChoice:
    """A role a user chose to practise, and when she last chose it."""

    role_id: str
    chosen_at: datetime


class RoleChoiceRepository(ABC):
    """History of the roles each user has chosen to practise (AC 3.4.1)."""

    @abstractmethod
    def record(self, owner_token_hash: str, role_id: str, chosen_at: datetime) -> None:
        """Remember that the owner chose this role now. Choosing a role
        again moves its date forward rather than adding a second entry."""
        raise NotImplementedError

    @abstractmethod
    def list_for_owner(self, owner_token_hash: str) -> list[RoleChoice]:
        """Every role the owner has chosen, most recently chosen first."""
        raise NotImplementedError
