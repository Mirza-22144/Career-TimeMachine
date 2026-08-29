from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.schemas.career_direction import CareerDirectionUpdate


@dataclass
class CareerDirection:
    """Internal career-direction selection stored for one profile."""

    return_readiness: str | None
    area_to_explore: str | None


class CareerDirectionService:
    """Business logic for reading and saving career-direction selections."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
    ) -> None:
        # Depend on interfaces so this stays compatible with a later DB repo.
        self.profiles = profiles
        self.catalogue = catalogue

    def get_for_session(self, session_token: str) -> CareerDirection:
        """Return the current direction selection for the session."""
        profile = self._get_or_create_profile(session_token)
        return CareerDirection(
            return_readiness=profile.return_readiness,
            area_to_explore=profile.area_to_explore,
        )

    def update_for_session(
        self,
        session_token: str,
        update: CareerDirectionUpdate,
    ) -> CareerDirection:
        """Validate and save whichever direction fields the client sent."""
        profile = self._get_or_create_profile(session_token)

        # exclude_unset preserves partial PATCH semantics.
        changes = update.model_dump(exclude_unset=True)
        self._validate_changes(changes)

        # Career-direction edits do not invalidate profile confirmation; only
        # PATCH /profile has that rule.
        for field_name, value in changes.items():
            setattr(profile, field_name, value)

        saved = self.profiles.save(profile)
        return CareerDirection(
            return_readiness=saved.return_readiness,
            area_to_explore=saved.area_to_explore,
        )

    def _get_or_create_profile(self, session_token: str) -> Profile:
        """Use the same one-profile-per-session rule as ProfileService."""
        profile = self.profiles.get_by_session_token(session_token)
        if profile is not None:
            return profile
        return self.profiles.save(Profile(session_token=session_token))

    def _validate_changes(self, changes: dict[str, Any]) -> None:
        """Validate catalogue-backed direction fields included in a PATCH."""
        if "return_readiness" in changes and changes["return_readiness"] is not None:
            self._require_catalogue_id(
                "return-statuses",
                changes["return_readiness"],
                "return_readiness",
            )

        if "area_to_explore" in changes and changes["area_to_explore"] is not None:
            self._require_catalogue_id(
                "career-areas",
                changes["area_to_explore"],
                "area_to_explore",
            )

    def _require_catalogue_id(
        self,
        catalogue_kind: str,
        item_id: str,
        field_name: str,
    ) -> None:
        """Reject a selection that is not in the relevant catalogue."""
        valid_ids = {item.id for item in self.catalogue.get_items(catalogue_kind)}
        if item_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: {item_id}",
            )
