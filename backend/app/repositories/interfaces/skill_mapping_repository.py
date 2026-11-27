from abc import ABC, abstractmethod


class SkillMappingRepository(ABC):
    """Storage contract for skill-to-career-area mappings.

    The repository returns career-area IDs only. The service resolves those IDs
    through the catalogue so labels stay in one place.
    """

    @abstractmethod
    def get_connected_areas(self, skill_id: str) -> list[str]:
        """Return connected career-area IDs for a catalogue skill ID."""
        raise NotImplementedError
