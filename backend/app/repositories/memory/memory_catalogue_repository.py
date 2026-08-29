from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)

# PROVISIONAL / MOCK data for Iteration 1. The data-science teammate replaces
# this with prepared PostgreSQL data later. Keep the ids stable.
_CATALOGUES: dict[str, list[CatalogueItem]] = {
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


class MemoryCatalogueRepository(CatalogueRepository):
    """DEVELOPMENT-ONLY curated catalogues (see _CATALOGUES above)."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        return _CATALOGUES.get(kind, [])   # [] for an unknown kind
