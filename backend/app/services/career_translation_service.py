from dataclasses import dataclass, field

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import ProfileRepository


@dataclass
class OwnedSkill:
    """A recorded skill, marked 'still relevant' if it is in demand for the
    user's previous role. This is not a claim about future demand."""

    id: str
    label: str
    still_relevant: bool


@dataclass
class NewHorizonSkill:
    id: str
    label: str


@dataclass
class SkillRelevanceMap:
    """Compares the user's recorded skills against the current in-demand
    skills for the same role. 'Skills You Bring Back' are what she already
    has; 'New Horizons' are in-demand skills for that role she has not
    recorded. This is not a skill-to-career-area mapping."""

    role_label: str | None
    role_data_available: bool
    owned_skills: list[OwnedSkill] = field(default_factory=list)
    custom_skills: list[str] = field(default_factory=list)
    new_horizons: list[NewHorizonSkill] = field(default_factory=list)


class CareerTranslationService:
    """Builds the Skill Relevance Map shown in step 4 of the wizard."""

    def __init__(self, profiles: ProfileRepository, catalogue: CatalogueRepository) -> None:
        # Depend on interfaces so each backing store can be replaced later.
        self.profiles = profiles
        self.catalogue = catalogue

    def build_for_session(self, session_token: str) -> SkillRelevanceMap:
        """Build the skill relevance map for one session. Used by the
        career-translation route."""
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None or profile.role_id is None:
            return SkillRelevanceMap(role_label=None, role_data_available=False)

        role_label = next(
            (r.label for r in self.catalogue.get_items("roles") if r.id == profile.role_id),
            profile.role_id,
        )
        role_skills = self.catalogue.get_skills_for_role(profile.role_id)
        if not role_skills:
            # No skill data for this role - the frontend shows "Current
            # skill demand information is unavailable for this role."
            return SkillRelevanceMap(
                role_label=role_label,
                role_data_available=False,
                custom_skills=profile.custom_skills,
            )

        role_in_demand_ids = {s.id for s in role_skills if s.in_demand}
        all_labels_by_id = {s.id: s.label for s in self.catalogue.get_items("skills")}
        owned_ids = set(profile.skill_ids)

        owned_skills = [
            OwnedSkill(
                id=skill_id,
                label=all_labels_by_id.get(skill_id, skill_id),
                still_relevant=skill_id in role_in_demand_ids,
            )
            for skill_id in profile.skill_ids
        ]
        new_horizons = [
            NewHorizonSkill(id=s.id, label=s.label)
            for s in role_skills
            if s.in_demand and s.id not in owned_ids
        ]

        return SkillRelevanceMap(
            role_label=role_label,
            role_data_available=True,
            owned_skills=owned_skills,
            custom_skills=profile.custom_skills,
            new_horizons=new_horizons,
        )
