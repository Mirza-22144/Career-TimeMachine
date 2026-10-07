from app.repositories.interfaces.vacancy_repository import (
    NATIONAL_STATE,
    RoleMarketData,
    VacancyRepository,
)


class MemoryVacancyRepository(VacancyRepository):
    """Fixed, in-memory market data for tests and local dev without a
    database. Empty by default (no mapping for any role) so predictions
    degrade gracefully with no market data, same as a genuinely unmapped
    role against the real database; tests inject fixed entries via
    `data` to exercise the "has market data" path deterministically."""

    def __init__(self, data: dict[tuple[str, str], RoleMarketData] | None = None) -> None:
        self._data = data or {}

    def get_for_role(self, role_id: str, state: str = NATIONAL_STATE) -> RoleMarketData | None:
        return self._data.get((role_id, state))
