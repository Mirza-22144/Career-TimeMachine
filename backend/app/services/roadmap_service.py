from dataclasses import dataclass, field
from datetime import datetime

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.practice_session_repository import PracticeSessionRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.services.practice_role_service import OTHER_ROLE_ID, PracticeRoleService
from app.services.role_prediction_service import RoleMarketDisplay, RolePredictionService

# Skills You Could Explore is a short, ordered path (Practised / Next /
# Later), not the role's whole skill list.
MAX_EXPLORE_SKILLS = 3


@dataclass
class RoadmapSkill:
    id: str | None  # None for a skill she typed in herself
    label: str


@dataclass
class ExploreSkill:
    """One step under Skills You Could Explore (AC 2.2.4). status is
    "practised", "next" or "later"; the single "next" skill is the practice
    focus."""

    id: str
    label: str
    status: str
    practised_on: datetime | None = None


@dataclass
class RoadmapRole:
    role_id: str
    role_label: str
    # False when the catalogue has no skills mapped to this role - the
    # frontend shows "Skill information isn't available for this role yet."
    skill_data_available: bool
    skills_bring_back: list[RoadmapSkill] = field(default_factory=list)
    skills_could_explore: list[ExploreSkill] = field(default_factory=list)
    market_data: RoleMarketDisplay | None = None


@dataclass
class Roadmap:
    """Your Roadmap (AC 2.2.3): the previous role and up to two suggested
    roles. previous_role is None until a previous role has been saved."""

    previous_role: RoadmapRole | None = None
    years_experience_label: str | None = None
    suggested_roles: list[RoadmapRole] = field(default_factory=list)
    selected_role_id: str | None = None


class RoadmapService:
    """Builds Your Roadmap from the profile, the role/skill catalogue, the
    two-role prediction and the practice history. Nothing here is scored or
    ranked - it describes roles, not the user."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        predictions: RolePredictionService,
        practice_roles: PracticeRoleService,
        practice_sessions: PracticeSessionRepository,
    ) -> None:
        self.profiles = profiles
        self.catalogue = catalogue
        self.predictions = predictions
        self.practice_roles = practice_roles
        self.practice_sessions = practice_sessions

    def build_for_session(self, session_token: str) -> Roadmap:
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None or profile.role_id is None:
            return Roadmap()

        role_labels = {item.id: item.label for item in self.catalogue.get_items("roles")}
        previous_label = role_labels.get(profile.role_id, profile.role_id)
        if profile.role_id == OTHER_ROLE_ID and profile.role_other_text:
            previous_label = profile.role_other_text

        all_skills = self.catalogue.get_items("skills")
        skill_labels = {item.id: item.label for item in all_skills}
        practised = self._practised_skills(session_token)

        previous = self._role(
            profile, profile.role_id, previous_label, skill_labels, len(all_skills), practised, is_previous=True
        )
        suggested = [
            self._role(profile, role.role_id, role.role_label, skill_labels, len(all_skills), practised)
            for role in self.predictions.predict_two_for_session(session_token).predicted_roles
        ]

        # A role she chose herself (closest to a job description, or from
        # See All Roles) that is neither her previous role nor one of the
        # suggestions still gets its own card, first in the list.
        selected_role_id = self.practice_roles.get_for_session(session_token).role_id
        shown = {previous.role_id} | {role.role_id for role in suggested}
        if selected_role_id and selected_role_id not in shown and selected_role_id in role_labels:
            suggested.insert(
                0,
                self._role(
                    profile, selected_role_id, role_labels[selected_role_id], skill_labels, len(all_skills), practised
                ),
            )

        years = {item.id: item.label for item in self.catalogue.get_items("experience-options")}
        return Roadmap(
            previous_role=previous,
            years_experience_label=years.get(profile.years_experience),
            suggested_roles=suggested,
            selected_role_id=selected_role_id,
        )

    def _role(
        self,
        profile: Profile,
        role_id: str,
        role_label: str,
        skill_labels: dict[str, str],
        total_skill_count: int,
        practised: dict[tuple[str, str], datetime],
        is_previous: bool = False,
    ) -> RoadmapRole:
        role_skills = self.catalogue.get_skills_for_role(role_id)
        # get_skills_for_role falls back to the whole skill list for a role
        # with nothing mapped to it, so "every skill" means "no data".
        has_data = role_id != OTHER_ROLE_ID and 0 < len(role_skills) < total_skill_count
        owned_ids = set(profile.skill_ids)

        own_skills = [
            RoadmapSkill(id=skill_id, label=skill_labels[skill_id])
            for skill_id in profile.skill_ids
            if skill_id in skill_labels
        ] + [RoadmapSkill(id=None, label=label) for label in profile.custom_skills]

        market = self.predictions.market_data_for(role_id)
        if not has_data:
            # AC 2.2.3 exception: show her own skills.
            return RoadmapRole(role_id, role_label, False, skills_bring_back=own_skills, market_data=market)

        role_skill_ids = {skill.id for skill in role_skills}
        # Her previous role shows everything she recorded; a suggested role
        # shows only the skills of hers that are listed for that role.
        bring_back = own_skills if is_previous else [s for s in own_skills if s.id in role_skill_ids]

        explore: list[ExploreSkill] = []
        next_assigned = False
        for skill in role_skills:
            if not skill.in_demand or skill.id in owned_ids:
                continue
            practised_on = practised.get((role_id, skill.label.casefold()))
            if practised_on is not None:
                status = "practised"
            elif not next_assigned:
                status, next_assigned = "next", True
            else:
                status = "later"
            explore.append(ExploreSkill(skill.id, skill.label, status, practised_on))
            if len(explore) == MAX_EXPLORE_SKILLS:
                break

        return RoadmapRole(role_id, role_label, True, bring_back, explore, market)

    def _practised_skills(self, session_token: str) -> dict[tuple[str, str], datetime]:
        """(role id, skill label) -> when it was first practised, taken from
        the skills tagged on each completed activity (AC 2.2.4)."""
        practised: dict[tuple[str, str], datetime] = {}
        for session in self.practice_sessions.list_for_owner(session_token):
            for scenario in session.scenarios:
                if scenario.status != "completed" or scenario.response is None:
                    continue
                tagged = list(scenario.skills_used)
                if scenario.new_skill_focus:
                    tagged.append(scenario.new_skill_focus)
                for label in tagged:
                    key = (session.role.id, label.casefold())
                    when = scenario.response.submitted_at
                    if key not in practised or when < practised[key]:
                        practised[key] = when
        return practised
