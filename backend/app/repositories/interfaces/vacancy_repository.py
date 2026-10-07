from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

# Several roles share one ANZSCO group (e.g. Software Developer, Computer
# Programmer and Blockchain Engineer can all show the same figure) - per
# DB 3.1's own note, callers must label this with anzsco_title and
# latest_month, never present it as ads for the exact predicted role.
NATIONAL_STATE = "AUST"


@dataclass(frozen=True)
class RoleMarketData:
    """Real Australian hiring-demand data for the ANZSCO group a role maps
    to - read-only reference data maintained by the data team's pipeline
    (data/pipeline/build_vacancy_seed.py), never written to by the app."""

    anzsco_code: str
    anzsco_title: str
    confidence: str  # "high" | "medium" | "low" - how good the role->ANZSCO match is
    state: str
    latest_month: date
    ads_latest: int
    ads_12m_avg: int
    yoy_change_pct: float | None  # null if there's no prior-year data to compare against


class VacancyRepository(ABC):
    """Reads real hiring-demand data for a role, where a mapping exists.

    Not every role has one yet (role_anzsco_map has no row for "other", and
    coverage can change as the data team's pipeline is rerun) - get_for_role
    returns None rather than raising when there is nothing to show.
    """

    @abstractmethod
    def get_for_role(self, role_id: str, state: str = NATIONAL_STATE) -> RoleMarketData | None:
        raise NotImplementedError
