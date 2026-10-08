from datetime import datetime

from app.repositories.interfaces.role_choice_repository import RoleChoice, RoleChoiceRepository


class MemoryRoleChoiceRepository(RoleChoiceRepository):
    """In-memory store for tests and local dev without a database."""

    def __init__(self) -> None:
        self._by_owner: dict[str, dict[str, datetime]] = {}

    def record(self, owner_token_hash: str, role_id: str, chosen_at: datetime) -> None:
        self._by_owner.setdefault(owner_token_hash, {})[role_id] = chosen_at

    def list_for_owner(self, owner_token_hash: str) -> list[RoleChoice]:
        choices = [
            RoleChoice(role_id=role_id, chosen_at=chosen_at)
            for role_id, chosen_at in self._by_owner.get(owner_token_hash, {}).items()
        ]
        return sorted(choices, key=lambda choice: choice.chosen_at, reverse=True)
