"""AC 2.2.4: Skills You Could Explore as Practised / Next / Later steps.
Skills her practice can cover come first, so what she is told to practise
next is something that can then be ticked."""

from datetime import datetime, timezone

from app.providers.scenario_provider import ScenarioProvider
from app.repositories.interfaces.catalogue_repository import CatalogueItem
from app.services.roadmap_service import RoadmapService

ROLE = "web_developer"
ROLE_SKILLS = [
    CatalogueItem(id="angular", label="Angular", in_demand=True),  # in demand, but no activity uses it
    CatalogueItem(id="bootstrap", label="Bootstrap"),
    CatalogueItem(id="css", label="CSS", in_demand=True),
    CatalogueItem(id="github", label="GitHub", in_demand=True),
    CatalogueItem(id="jenkins", label="Jenkins"),
    CatalogueItem(id="react", label="React", in_demand=True),  # she already has it
    CatalogueItem(id="zeplin", label="Zeplin"),  # neither in demand nor practisable
]


class PoolWith(ScenarioProvider):
    def __init__(self, *skills):
        self.skills = list(skills)

    def skills_for_role(self, role_id):
        return self.skills

    def generate_scenario(self, request):
        raise NotImplementedError

    def generate_feedback(self, request):
        raise NotImplementedError


def _steps(practised_labels=(), provider=None):
    service = RoadmapService(None, None, None, None, None, scenarios=provider or PoolWith("Bootstrap", "Github", "Jenkins"))
    practised = {
        (ROLE, label.casefold()): datetime(2026, 10, day, tzinfo=timezone.utc)
        for day, label in enumerate(practised_labels, start=1)
    }
    return [(s.label, s.status) for s in service._explore_steps(ROLE, ROLE_SKILLS, {"react"}, practised)]


def test_skills_her_practice_covers_come_first():
    assert _steps() == [("Bootstrap", "next"), ("GitHub", "later"), ("Jenkins", "later")]


def test_a_practised_skill_is_ticked_and_the_next_one_moves_on():
    assert _steps(["Bootstrap"]) == [("Bootstrap", "practised"), ("GitHub", "next"), ("Jenkins", "later")]


def test_the_most_recently_practised_skill_stays_in_view():
    steps = _steps(["Bootstrap", "GitHub", "Jenkins"])

    # Everything her practice covers is done: in-demand skills follow.
    assert steps == [("Jenkins", "practised"), ("Angular", "next"), ("CSS", "later")]


def test_without_practice_coverage_in_demand_skills_are_listed_as_before():
    assert _steps(provider=PoolWith()) == [("Angular", "next"), ("CSS", "later"), ("GitHub", "later")]


def test_skills_she_has_or_that_are_neither_in_demand_nor_practisable_are_left_out():
    labels = [label for label, _ in _steps(provider=PoolWith())] + [label for label, _ in _steps()]

    assert "React" not in labels
    assert "Zeplin" not in labels


def test_the_focus_of_the_latest_activity_is_the_practised_step_shown():
    """One activity ticks several skills. The one kept in view is its focus:
    the earliest of them in the roadmap's order."""
    from app.services.roadmap_service import PractisedSkills

    practised = PractisedSkills()
    started = datetime(2026, 10, 9, 9, 0, tzinfo=timezone.utc)
    # Answered in this order within one activity: the focus question first.
    for minute, label in enumerate(["Bootstrap", "Jenkins"], start=1):
        key = (ROLE, label.casefold())
        practised[key] = datetime(2026, 10, 9, 9, minute, tzinfo=timezone.utc)
        practised.activity_started[key] = started
    service = RoadmapService(None, None, None, None, None, scenarios=PoolWith("Bootstrap", "Github", "Jenkins"))

    steps = [(s.label, s.status) for s in service._explore_steps(ROLE, ROLE_SKILLS, {"react"}, practised)]

    assert steps == [("Bootstrap", "practised"), ("GitHub", "next"), ("Angular", "later")]
