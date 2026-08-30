from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)

# PROVISIONAL / MOCK data for Iteration 1. The data-science teammate replaces
# this with prepared PostgreSQL data later. Keep the ids stable.
CATALOGUES: dict[str, list[CatalogueItem]] = {
    "roles": [
        CatalogueItem("software_engineer", "Software Engineer"),
        CatalogueItem("software_developer", "Software Developer"),
        CatalogueItem("systems_analyst", "Systems Analyst"),
        CatalogueItem("qa_engineer", "QA Engineer"),
        CatalogueItem("web_developer", "Web Developer"),
        CatalogueItem("other", "Other"),
    ],
    "experience-options": [                      # fixed set from the document
        CatalogueItem("1", "1 year"),
        CatalogueItem("2", "2 years"),
        CatalogueItem("3", "3 years"),
        CatalogueItem("5", "5 years"),
        CatalogueItem("7", "7 years"),
        CatalogueItem("10_plus", "10+ years"),
    ],
    "skills": [
        CatalogueItem("java", "Java"),
        CatalogueItem("python", "Python"),
        CatalogueItem("rest_apis", "REST APIs"),
        CatalogueItem("aws", "AWS"),
        CatalogueItem("sql", "SQL"),
        CatalogueItem("git", "Git"),
        CatalogueItem("react", "React"),
        CatalogueItem("docker", "Docker"),
    ],
    "responsibilities": [
        CatalogueItem("backend_development", "Backend development"),
        CatalogueItem("api_design", "API design"),
        CatalogueItem("debugging", "Debugging"),
        CatalogueItem("testing", "Testing"),
        CatalogueItem("code_review", "Code review"),
        CatalogueItem("system_design", "System design"),
    ],
    "break-reasons": [
        CatalogueItem("caregiving", "Caregiving"),
        CatalogueItem("personal", "Personal reasons"),
        CatalogueItem("health_wellbeing", "Health and wellbeing"),
        CatalogueItem("further_study", "Further study"),
        CatalogueItem("relocation", "Relocation"),
        CatalogueItem("other", "Other"),
        CatalogueItem("prefer_not_to_say", "Prefer not to say"),
    ],
    "return-statuses": [
        CatalogueItem("ready", "I'm ready to return"),
        CatalogueItem("preparing", "I'm preparing to return"),
        CatalogueItem("planning_soon", "I'm planning to return soon"),
        CatalogueItem("not_sure", "I'm not sure yet"),
    ],
    "career-areas": [
        CatalogueItem("ai_assisted_development", "AI-assisted Development"),
        CatalogueItem("cloud_native_engineering", "Cloud-Native Engineering"),
        CatalogueItem("modern_devops", "Modern DevOps Practices"),
        CatalogueItem("data_analytics_basics", "Data & Analytics Basics"),
    ],
}


# PLACEHOLDER for role_skill (DATA_HANDOVER.md 4.1) until the real 1,299-skill
# / 5,629-row role_skill table is connected. Reuses the flat skills list above
# with representative in_demand/hot_technology flags per role, just so the
# frontend's role-dependent fetch + ordering has something real to call.
_SKILLS_BY_ROLE: dict[str, list[CatalogueItem]] = {
    "software_engineer": [
        CatalogueItem("python", "Python", in_demand=True, hot_technology=True),
        CatalogueItem("react", "React", in_demand=True, hot_technology=True),
        CatalogueItem("rest_apis", "REST APIs", in_demand=True),
        CatalogueItem("git", "Git", in_demand=True),
        CatalogueItem("aws", "AWS", hot_technology=True),
        CatalogueItem("docker", "Docker"),
        CatalogueItem("java", "Java"),
        CatalogueItem("sql", "SQL"),
    ],
    "software_developer": [
        CatalogueItem("java", "Java", in_demand=True),
        CatalogueItem("sql", "SQL", in_demand=True),
        CatalogueItem("git", "Git", in_demand=True),
        CatalogueItem("rest_apis", "REST APIs", hot_technology=True),
        CatalogueItem("python", "Python", hot_technology=True),
        CatalogueItem("docker", "Docker"),
        CatalogueItem("react", "React"),
        CatalogueItem("aws", "AWS"),
    ],
    "systems_analyst": [
        CatalogueItem("sql", "SQL", in_demand=True, hot_technology=True),
        CatalogueItem("rest_apis", "REST APIs", in_demand=True),
        CatalogueItem("git", "Git"),
        CatalogueItem("aws", "AWS"),
        CatalogueItem("java", "Java"),
    ],
    "qa_engineer": [
        CatalogueItem("git", "Git", in_demand=True, hot_technology=True),
        CatalogueItem("java", "Java", in_demand=True),
        CatalogueItem("python", "Python", hot_technology=True),
        CatalogueItem("rest_apis", "REST APIs"),
        CatalogueItem("docker", "Docker"),
    ],
    "web_developer": [
        CatalogueItem("react", "React", in_demand=True, hot_technology=True),
        CatalogueItem("rest_apis", "REST APIs", in_demand=True),
        CatalogueItem("git", "Git", in_demand=True),
        CatalogueItem("sql", "SQL"),
        CatalogueItem("aws", "AWS"),
        CatalogueItem("docker", "Docker"),
    ],
}


class MemoryCatalogueRepository(CatalogueRepository):
    """DEVELOPMENT-ONLY curated catalogues (see CATALOGUES above)."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        return CATALOGUES.get(kind, [])   # [] for an unknown kind

    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        items = _SKILLS_BY_ROLE.get(role_id, CATALOGUES["skills"]) if role_id else CATALOGUES["skills"]
        return sorted(items, key=lambda s: (not s.in_demand, not s.hot_technology, s.label))
