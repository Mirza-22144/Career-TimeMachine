from dataclasses import dataclass

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.skill_mapping_repository import SkillMappingRepository


@dataclass
class NamedItem:
    """Internal id + name pair used by career-translation responses."""

    id: str
    name: str


@dataclass
class SkillTranslation:
    """Internal translation result for one selected catalogue skill."""

    previous_skill: NamedItem
    connected_areas: list[NamedItem]


class CareerTranslationService:
    """Business logic for deterministic skill-to-career-area translations."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        skill_mappings: SkillMappingRepository,
    ) -> None:
        # Depend on interfaces so each backing store can be replaced later.
        self.profiles = profiles
        self.catalogue = catalogue
        self.skill_mappings = skill_mappings

    def build_all_for_session(self, session_token: str) -> list[SkillTranslation]:
        """Build translations for every catalogue skill selected by the user."""
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None:
            return []

        # Custom skills are intentionally ignored because they have no stable
        # catalogue ID and therefore no deterministic mapping.
        return [
            self._build_for_selected_skill(skill_id)
            for skill_id in profile.skill_ids
        ]

    def build_one_for_session(
        self,
        session_token: str,
        skill_id: str,
    ) -> SkillTranslation:
        """Build one translation, only if the skill is in the user's profile."""
        profile = self.profiles.get_by_session_token(session_token)

        if profile is None or skill_id not in profile.skill_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="skill not selected",
            )

        return self._build_for_selected_skill(skill_id)

    def _build_for_selected_skill(self, skill_id: str) -> SkillTranslation:
        """Resolve one selected skill and its mapped career areas."""
        connected_area_ids = self.skill_mappings.get_connected_areas(skill_id)

        return SkillTranslation(
            previous_skill=self._required_named_item("skills", skill_id),
            connected_areas=[
                self._required_named_item("career-areas", area_id)
                for area_id in connected_area_ids
            ],
        )

    def _required_named_item(self, catalogue_kind: str, item_id: str) -> NamedItem:
        """Resolve a catalogue ID into id + name, failing on inconsistent data."""
        names_by_id = {
            item.id: item.label
            for item in self.catalogue.get_items(catalogue_kind)
        }

        if item_id not in names_by_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Missing catalogue item for {catalogue_kind}: {item_id}",
            )

        return NamedItem(id=item_id, name=names_by_id[item_id])
