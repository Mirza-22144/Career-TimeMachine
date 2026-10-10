import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.providers.scenario_provider import ScenarioProvider
from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.practice_session_repository import PracticeSessionRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.repositories.interfaces.role_choice_repository import RoleChoiceRepository
from app.services.practice_role_service import OTHER_ROLE_ID, PracticeRoleService
from app.services.role_prediction_service import RoleExplanation, RoleMarketDisplay, RolePredictionService

logger = logging.getLogger(__name__)

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
    # Why the model suggested this role; None for her previous role and for
    # a role she picked herself.
    explanation: RoleExplanation | None = None


@dataclass
class ChosenRole:
    """A role she has chosen to practise, for the dashboard (AC 3.4.1)."""

    role_id: str
    role_label: str
    chosen_at: datetime


@dataclass
class Roadmap:
    """Your Roadmap (AC 2.2.3): the previous role and up to two suggested
    roles. previous_role is None until a previous role has been saved."""

    previous_role: RoadmapRole | None = None
    years_experience_label: str | None = None
    suggested_roles: list[RoadmapRole] = field(default_factory=list)
    selected_role_id: str | None = None
    chosen_roles: list[ChosenRole] = field(default_factory=list)


class PractisedSkills(dict):
    """(role id, skill label) -> when the skill was first practised.
    activity_started gives, for the same keys, when the activity it was
    practised in began, so skills from one activity can be kept together."""

    def __init__(self) -> None:
        super().__init__()
        self.activity_started: dict[tuple[str, str], datetime] = {}


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
        role_choices: RoleChoiceRepository | None = None,
        scenarios: ScenarioProvider | None = None,
    ) -> None:
        self.profiles = profiles
        self.catalogue = catalogue
        self.predictions = predictions
        self.practice_roles = practice_roles
        self.practice_sessions = practice_sessions
        self.role_choices = role_choices
        # Tells the roadmap which skills her practice can actually cover.
        self.scenarios = scenarios

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
        suggested = []
        for role in self.predictions.predict_two_for_profile(profile).predicted_roles:
            card = self._role(profile, role.role_id, role.role_label, skill_labels, len(all_skills), practised)
            card.explanation = role.explanation
            suggested.append(card)

        # A role she chose herself (closest to a job description, or from
        # See All Roles) that is neither her previous role nor one of the
        # suggestions still gets its own card, first in the list.
        selected_role_id = self.practice_roles.get_for_profile(profile).role_id
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
            chosen_roles=self._chosen_roles(session_token, role_labels),
        )

    def _chosen_roles(self, session_token: str, role_labels: dict[str, str]) -> list[ChosenRole]:
        """Her dated role history, newest first. Empty rather than an error
        if the history can't be read - the roadmap itself doesn't depend on it."""
        if self.role_choices is None:
            return []
        try:
            choices = self.role_choices.list_for_owner(session_token)
        except Exception:
            logger.warning("Could not read role choice history", exc_info=True)
            return []
        return [
            ChosenRole(choice.role_id, role_labels[choice.role_id], choice.chosen_at)
            for choice in choices
            if choice.role_id in role_labels
        ]

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

        explore = self._explore_steps(role_id, role_skills, owned_ids, practised)

        return RoadmapRole(role_id, role_label, True, bring_back, explore, market)

    def _explore_steps(
        self,
        role_id: str,
        role_skills: list,
        owned_ids: set[str],
        practised: dict[tuple[str, str], datetime],
    ) -> list[ExploreSkill]:
        """Skills You Could Explore as Practised / Next / Later steps
        (AC 2.2.4): skills of the role she doesn't have, limited to
        MAX_EXPLORE_SKILLS.

        Skills her practice activities are tagged with come first, so the
        next skill is one she can really practise and then see ticked -
        an in-demand skill no activity uses could never be marked practised.
        What is shown is a window around the next skill: the most recently
        practised one(s) before it and what comes after it."""
        practisable = {label.casefold() for label in self.scenarios.skills_for_role(role_id)} if self.scenarios else set()
        candidates = [
            skill
            for skill in role_skills
            if skill.id not in owned_ids and (skill.in_demand or skill.label.casefold() in practisable)
        ]
        # Practised skills in the order to show them: by the activity they
        # were practised in, and within one activity its focus last - the
        # focus is the earliest candidate the activity used (see
        # PracticeSessionService._put_focus_first), so reversing the
        # catalogue order puts it at the end, next to the "next" step.
        activity_started = getattr(practised, "activity_started", {})
        order = {skill.id: index for index, skill in enumerate(candidates)}

        def shown_after(skill) -> tuple:
            key = (role_id, skill.label.casefold())
            return (activity_started.get(key, practised[key]), -order[skill.id])

        done = sorted((skill for skill in candidates if (role_id, skill.label.casefold()) in practised), key=shown_after)
        # sorted() is stable, so each group keeps the catalogue's order.
        to_do = sorted(
            (skill for skill in candidates if (role_id, skill.label.casefold()) not in practised),
            key=lambda skill: skill.label.casefold() not in practisable,
        )

        steps = [
            ExploreSkill(skill.id, skill.label, "practised", practised[(role_id, skill.label.casefold())])
            for skill in done
        ] + [
            ExploreSkill(skill.id, skill.label, "next" if index == 0 else "later", None)
            for index, skill in enumerate(to_do)
        ]
        # Keep one practised step in view when there is a next and a later
        # one to show beside it; otherwise simply the last few.
        start = max(0, len(done) - (MAX_EXPLORE_SKILLS - 2 if len(to_do) >= 2 else MAX_EXPLORE_SKILLS - len(to_do)))
        start = max(0, min(start, len(steps) - MAX_EXPLORE_SKILLS))
        return steps[start : start + MAX_EXPLORE_SKILLS]

    def _practised_skills(self, session_token: str) -> "PractisedSkills":
        """(role id, skill label) -> when it was first practised, taken from
        the skills tagged on each completed activity (AC 2.2.4)."""
        practised = PractisedSkills()
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
                        practised.activity_started[key] = session.created_at
        return practised
