from app.repositories.interfaces.skill_mapping_repository import SkillMappingRepository


# Placeholder skill-to-career-area links, picked by hand for now.
# Only catalogue skill ids appear here. Custom skills the user typed in
# have no mapping since they have no stable id to match against.
_SKILL_TO_CAREER_AREA_IDS: dict[str, list[str]] = {
    "python": ["data_analytics_basics"],
    "rest_apis": ["cloud_native_engineering"],
    "aws": ["cloud_native_engineering"],
    "sql": ["data_analytics_basics"],
    "git": ["modern_devops"],
    "docker": ["modern_devops", "cloud_native_engineering"],
}


class MemorySkillMappingRepository(SkillMappingRepository):
    """Skill mapping store backed by the hand-picked list above, used until
    real skill-to-career-area data is loaded. Not currently used by any
    route - kept in case a future feature needs this kind of mapping."""

    def get_connected_areas(self, skill_id: str) -> list[str]:
        """Return the career-area ids linked to a skill, or [] if none."""
        return _SKILL_TO_CAREER_AREA_IDS.get(skill_id, [])
