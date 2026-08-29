from app.repositories.interfaces.skill_mapping_repository import SkillMappingRepository


# PROVISIONAL / MOCK deterministic mappings for Iteration 1.
# Only catalogue skill IDs appear here. Custom user skills intentionally have
# no mappings because they are not stable catalogue identifiers.
_SKILL_TO_CAREER_AREA_IDS: dict[str, list[str]] = {
    "python": ["data_analytics_basics"],
    "rest_apis": ["cloud_native_engineering"],
    "aws": ["cloud_native_engineering"],
    "sql": ["data_analytics_basics"],
    "git": ["modern_devops"],
    "docker": ["modern_devops", "cloud_native_engineering"],
}


class MemorySkillMappingRepository(SkillMappingRepository):
    """DEVELOPMENT-ONLY skill mapping store.

    These mappings are hand-curated placeholders so the frontend can build the
    flow before the data-prep handover. They are deterministic and make no AI
    calls.
    """

    def get_connected_areas(self, skill_id: str) -> list[str]:
        """Return mapped career-area IDs, or [] when no mapping exists."""
        return _SKILL_TO_CAREER_AREA_IDS.get(skill_id, [])
