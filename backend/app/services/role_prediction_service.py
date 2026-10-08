import logging
from dataclasses import dataclass, field
from datetime import date

from pydantic import ValidationError

from app.core.vacancy_rounding import round_to_range
from app.providers.role_prediction_provider import (
    PredictedRoleContent,
    RolePredictionProvider,
    RolePredictionProviderError,
    RolePredictionRequest,
    SkillContext,
)
from app.providers.two_role_prediction_provider import (
    PredictedRolesContent,
    TwoRolePredictionProvider,
    TwoRolePredictionProviderError,
)
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.repositories.interfaces.vacancy_repository import RoleMarketData, VacancyRepository
from app.services.practice_role_service import OTHER_ROLE_ID

logger = logging.getLogger(__name__)


@dataclass
class PredictedRole:
    """The predicted role for a session, or nulls when none is available."""

    role_id: str | None
    role_label: str | None


_UNAVAILABLE = PredictedRole(role_id=None, role_label=None)


@dataclass
class RoleMarketDisplay:
    """Display-ready market data - the raw RoleMarketData (repository,
    exact figures) rounded into a range at this layer, never exposed exact
    (industry mentor's guidance). Built from ads_12m_avg, not ads_latest -
    see MarketDataResponse's docstring for why."""

    anzsco_code: str
    anzsco_title: str
    confidence: str
    state: str
    latest_month: date
    ads_range_low: int
    ads_range_high: int
    yoy_change_pct: float | None


def _to_display(market: RoleMarketData) -> RoleMarketDisplay:
    vacancy_range = round_to_range(market.ads_12m_avg)
    return RoleMarketDisplay(
        anzsco_code=market.anzsco_code,
        anzsco_title=market.anzsco_title,
        confidence=market.confidence,
        state=market.state,
        latest_month=market.latest_month,
        ads_range_low=vacancy_range.low,
        ads_range_high=vacancy_range.high,
        yoy_change_pct=market.yoy_change_pct,
    )


@dataclass
class PredictedRoleWithMarketData:
    """One of the two Iteration 3 predicted roles (BE 3.4), with real
    Australian hiring-demand data where a role->ANZSCO mapping exists."""

    role_id: str
    role_label: str
    market_data: RoleMarketDisplay | None


@dataclass
class PredictedRolesResult:
    """Zero or two predicted roles for a session - never one. Empty when
    no prediction is available yet, same "never raise, resolve to empty"
    convention as the single-role predict_for_session."""

    predicted_roles: list[PredictedRoleWithMarketData] = field(default_factory=list)


class RolePredictionService:
    """Predicts a future IT role from the profile's previous role and
    skills. Never raises for "no prediction yet" or a model failure - both
    resolve to null fields, matching PracticeRoleResponse's convention, so
    the frontend can treat this as a purely optional suggestion."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        provider: RolePredictionProvider,
        two_role_provider: TwoRolePredictionProvider | None = None,
        vacancy: VacancyRepository | None = None,
    ) -> None:
        self.profiles = profiles
        self.catalogue = catalogue
        self.provider = provider
        # Both optional: only predict_two_for_session (BE 3.4) needs them,
        # and the existing GET /predicted-role (singular) construction site
        # shouldn't be forced to supply dependencies it never uses.
        self.two_role_provider = two_role_provider
        self.vacancy = vacancy

    def predict_for_session(self, session_token: str) -> PredictedRole:
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None or profile.role_id is None:
            return _UNAVAILABLE

        role_label = self._role_label(profile.role_id, profile.role_other_text)
        if role_label is None:
            return _UNAVAILABLE

        request = RolePredictionRequest(
            role_id=profile.role_id,
            role_label=role_label,
            skills=self._skill_context(profile.skill_ids, profile.custom_skills),
        )

        try:
            raw = self.provider.predict(request)
            content = PredictedRoleContent.model_validate(raw)
        except (RolePredictionProviderError, ValidationError) as exc:
            # Log the failure type only - never career context or model output.
            logger.warning("Role prediction provider could not supply a prediction (%s)", type(exc).__name__)
            return _UNAVAILABLE

        return PredictedRole(role_id=content.role_id, role_label=content.role_label)

    def predict_two_for_session(self, session_token: str) -> PredictedRolesResult:
        """BE 3.4: two predicted roles (AI 3.2's Version 2 model), each
        enriched with real Australian hiring-demand data where the role has
        an ANZSCO mapping (DB 3.1) - market_data is None for a role with no
        mapping yet (e.g. "other"), never fabricated. Never raises; resolves
        to an empty list for "no prediction yet" or a model failure, same
        convention as predict_for_session."""
        return self.predict_two_for_profile(self.profiles.get_by_session_token(session_token))

    def predict_two_for_profile(self, profile: Profile | None) -> PredictedRolesResult:
        """Same as predict_two_for_session for a profile the caller has
        already loaded, so it isn't read from storage a second time."""
        if profile is None or profile.role_id is None or self.two_role_provider is None:
            return PredictedRolesResult()

        role_label = self._role_label(profile.role_id, profile.role_other_text)
        if role_label is None:
            return PredictedRolesResult()

        request = RolePredictionRequest(
            role_id=profile.role_id,
            role_label=role_label,
            skills=self._skill_context(profile.skill_ids, profile.custom_skills),
        )

        try:
            raw = self.two_role_provider.predict(request)
            content = PredictedRolesContent.model_validate(raw)
        except (TwoRolePredictionProviderError, ValidationError) as exc:
            logger.warning(
                "Two-role prediction provider could not supply predictions (%s)", type(exc).__name__
            )
            return PredictedRolesResult()

        return PredictedRolesResult(
            predicted_roles=[
                PredictedRoleWithMarketData(
                    role_id=role.role_id,
                    role_label=role.role_label,
                    market_data=self.market_data_for(role.role_id),
                )
                for role in content.predicted_roles
            ]
        )

    def market_data_for(self, role_id: str) -> RoleMarketDisplay | None:
        if self.vacancy is None:
            return None
        market = self.vacancy.get_for_role(role_id)
        return _to_display(market) if market is not None else None

    def _role_label(self, role_id: str, role_other_text: str | None) -> str | None:
        if role_id == OTHER_ROLE_ID:
            return role_other_text or None
        labels = {item.id: item.label for item in self.catalogue.get_items("roles")}
        return labels.get(role_id)

    def _skill_context(self, skill_ids: list[str], custom_skills: list[str]) -> tuple[SkillContext, ...]:
        labels = {item.id: item.label for item in self.catalogue.get_items("skills")}
        catalogue_skills = [
            SkillContext(id=skill_id, label=labels[skill_id]) for skill_id in skill_ids if skill_id in labels
        ]
        custom = [SkillContext(id=None, label=skill) for skill in custom_skills]
        return tuple(catalogue_skills + custom)
