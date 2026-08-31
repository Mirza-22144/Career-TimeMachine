from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)

# Placeholder data for the catalogue kinds whose real database tables are
# still empty. roles and skills are not here - those always come from the
# real database once it is connected (see PostgresCatalogueRepository).
# Ids need to stay the same once the data team fills the real tables in.
CATALOGUES: dict[str, list[CatalogueItem]] = {
    "experience-options": [                      # fixed set from the document
        CatalogueItem("1", "1 year"),
        CatalogueItem("2", "2 years"),
        CatalogueItem("3", "3 years"),
        CatalogueItem("5", "5 years"),
        CatalogueItem("7", "7 years"),
        CatalogueItem("10_plus", "10+ years"),
    ],
    "responsibilities": [               # matches the 8 the data team plans to add; table is empty for now
        CatalogueItem("backend_development", "Backend development"),
        CatalogueItem("api_design", "API design"),
        CatalogueItem("debugging", "Debugging & troubleshooting"),
        CatalogueItem("testing", "Testing & QA"),
        CatalogueItem("code_review", "Code review"),
        CatalogueItem("system_design", "System design"),
        CatalogueItem("team_collaboration", "Team collaboration"),
        CatalogueItem("project_delivery", "Project delivery"),
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
    """Catalogue backed only by the placeholder lists above. Used when no
    database is connected. Without a database, roles and skills have no
    data source at all, so those kinds return an empty list."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        """Return the placeholder list for a kind, or [] if it is unknown
        (this includes roles and skills, which have no placeholder)."""
        return CATALOGUES.get(kind, [])

    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        """Always returns [] - there is no skill data without a database."""
        return self.get_items("skills")
