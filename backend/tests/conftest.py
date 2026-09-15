"""Shared test setup.

Roles and skills normally come from the real database, and the in-memory
fallback has no data for them, so API tests that use role or skill IDs fail
on a machine without a database .env. Every test runs against this small,
fixed catalogue instead, which keeps the suite deterministic and offline.
"""

import pytest

from app.api import dependencies
from app.main import app
from app.repositories.interfaces.catalogue_repository import CatalogueItem
from app.repositories.memory.memory_catalogue_repository import MemoryCatalogueRepository

TEST_ROLES = [
    CatalogueItem("software_engineer", "Software Engineer"),
    CatalogueItem("web_developer", "Web Developer"),
    CatalogueItem("qa_engineer", "QA Engineer"),
    CatalogueItem("data_analyst", "Data Analyst"),
    CatalogueItem("other", "Other"),
]

TEST_SKILLS = [
    CatalogueItem("python", "Python", in_demand=True, hot_technology=True),
    CatalogueItem("rest_apis", "REST APIs", in_demand=True),
    CatalogueItem("git", "Git", in_demand=True, hot_technology=True),
    CatalogueItem("react", "React", in_demand=True, hot_technology=True),
    CatalogueItem("aws", "AWS", hot_technology=True),
    CatalogueItem("sql", "SQL", in_demand=True),
]

# role_id -> linked skill ids, standing in for the role_skill table.
TEST_ROLE_SKILLS = {
    "software_engineer": ["python", "rest_apis", "git", "aws"],
    "web_developer": ["react", "git", "aws"],
    "qa_engineer": ["git", "python"],
    "data_analyst": ["sql", "python"],
}


class FakeCatalogueRepository(MemoryCatalogueRepository):
    """Placeholder catalogues plus fixed roles, skills and role links."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        if kind == "roles":
            return list(TEST_ROLES)
        if kind == "skills":
            return list(TEST_SKILLS)
        return super().get_items(kind)

    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        skills_by_id = {skill.id: skill for skill in TEST_SKILLS}
        linked = [skills_by_id[skill_id] for skill_id in TEST_ROLE_SKILLS.get(role_id or "", [])]
        if not linked:
            return list(TEST_SKILLS)
        return sorted(
            linked,
            key=lambda s: (not s.in_demand, not s.hot_technology, s.label.lower()),
        )


@pytest.fixture(autouse=True)
def fake_catalogue(monkeypatch):
    """Swap the shared catalogue repository for the fixed test catalogue."""
    repository = FakeCatalogueRepository()
    monkeypatch.setattr(dependencies, "_catalogue_repository", repository)
    return repository


@pytest.fixture
def use_provider():
    """Swap the workplace-scenario provider for one test."""

    def _use(provider) -> None:
        app.dependency_overrides[dependencies.get_scenario_provider] = lambda: provider

    yield _use
    app.dependency_overrides.pop(dependencies.get_scenario_provider, None)


@pytest.fixture
def use_activity_type():
    """Switch the activity type new practice scenarios use for one test."""

    def _use(activity_type: str) -> None:
        app.dependency_overrides[dependencies.get_practice_activity_type] = lambda: activity_type

    yield _use
    app.dependency_overrides.pop(dependencies.get_practice_activity_type, None)
