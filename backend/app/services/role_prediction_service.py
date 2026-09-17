import logging
from dataclasses import dataclass

from pydantic import ValidationError

from app.providers.role_prediction_provider import (
    PredictedRoleContent,
    RolePredictionProvider,
    RolePredictionProviderError,
    RolePredictionRequest,
    SkillContext,
)
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.services.practice_role_service import OTHER_ROLE_ID

logger = logging.getLogger(__name__)


@dataclass
class PredictedRole:
    """The predicted role for a session, or nulls when none is available."""

    role_id: str | None
    role_label: str | None


_UNAVAILABLE = PredictedRole(role_id=None, role_label=None)


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
    ) -> None:
        self.profiles = profiles
        self.catalogue = catalogue
        self.provider = provider

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
