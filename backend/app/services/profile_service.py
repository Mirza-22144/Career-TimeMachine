from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.schemas.profile import ProfileUpdate


class ProfileService:
    """Business logic for profile capture, confirmation, and deletion."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
    ) -> None:
        # Depend on repository interfaces so storage can be swapped later.
        self.profiles = profiles
        self.catalogue = catalogue

    def get_or_create(self, session_token: str) -> Profile:
        """Return the session's profile, creating an empty one if needed."""
        existing = self.profiles.get_by_session_token(session_token)
        if existing is not None:
            return existing

        # New sessions start with an empty, unconfirmed profile.
        return self.profiles.save(Profile(session_token=session_token))

    def update_profile(self, session_token: str, update: ProfileUpdate) -> Profile:
        """Apply a partial profile update and save the result."""
        profile = self.get_or_create(session_token)

        # Only apply fields the client actually sent.
        changes = update.model_dump(exclude_unset=True)

        # Validate catalogue IDs before mutating the profile.
        self._validate_changes(changes)

        # Clean free-text lists so storage stays predictable.
        for field_name in ("custom_skills", "custom_responsibilities"):
            if field_name in changes and changes[field_name] is not None:
                changes[field_name] = self._clean_custom_list(changes[field_name])

        # Empty strings should not count as useful "other" text.
        for field_name in ("role_other_text", "break_reason_other_text"):
            if field_name in changes and changes[field_name] is not None:
                changes[field_name] = changes[field_name].strip() or None

        # If the user is unsure about their return date, do not store a stale
        # planned date from an earlier edit.
        if changes.get("return_date_unsure") is True:
            changes["planned_return_date"] = None

        # Apply the validated changes to the dataclass.
        for field_name, value in changes.items():
            setattr(profile, field_name, value)

        # Re-check the cross-field date rule after all fields are applied.
        self._validate_date_rule(profile)

        # Any profile edit invalidates a previous confirmation.
        profile.confirmed = False
        profile.break_duration_months = self._calculate_break_duration_months(profile)

        return self.profiles.save(profile)

    def confirm_profile(self, session_token: str) -> Profile:
        """Confirm the profile if all required fields are complete."""
        profile = self.get_or_create(session_token)
        missing = self._missing_confirmation_fields(profile)

        if missing:
            # core/exceptions.py turns this into the standard error envelope.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PROFILE_INCOMPLETE",
                    "message": "Profile is incomplete",
                    "details": missing,
                },
            )

        profile.confirmed = True
        profile.break_duration_months = self._calculate_break_duration_months(profile)
        return self.profiles.save(profile)

    def delete_profile(self, session_token: str) -> None:
        """Delete the current session's profile if it exists."""
        self.profiles.delete_by_session_token(session_token)

    def _validate_changes(self, changes: dict[str, Any]) -> None:
        """Validate each catalogue-backed field included in a PATCH."""
        single_catalogue_fields = {
            "role_id": "roles",
            "years_experience": "experience-options",
            "break_reason": "break-reasons",
        }
        list_catalogue_fields = {
            "skill_ids": "skills",
            "responsibility_ids": "responsibilities",
        }

        for field_name, catalogue_kind in single_catalogue_fields.items():
            if field_name in changes and changes[field_name] is not None:
                self._require_catalogue_id(catalogue_kind, changes[field_name], field_name)

        for field_name, catalogue_kind in list_catalogue_fields.items():
            if field_name in changes and changes[field_name] is not None:
                for item_id in changes[field_name]:
                    self._require_catalogue_id(catalogue_kind, item_id, field_name)

    def _require_catalogue_id(
        self,
        catalogue_kind: str,
        item_id: str,
        field_name: str,
    ) -> None:
        """Reject IDs that do not exist in the relevant catalogue."""
        valid_ids = {item.id for item in self.catalogue.get_items(catalogue_kind)}
        if item_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: {item_id}",
            )

    def _validate_date_rule(self, profile: Profile) -> None:
        """The planned return date cannot be before the break start date."""
        if (
            profile.break_started_on is not None
            and profile.planned_return_date is not None
            and profile.planned_return_date < profile.break_started_on
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="planned_return_date must be on or after break_started_on",
            )

    def _missing_confirmation_fields(self, profile: Profile) -> list[str]:
        """Return field names that stop the profile from being confirmed."""
        missing: list[str] = []

        if profile.role_id is None:
            missing.append("role_id")
        elif profile.role_id == "other" and not profile.role_other_text:
            missing.append("role_other_text")

        if profile.years_experience is None:
            missing.append("years_experience")

        if profile.break_reason == "other" and not profile.break_reason_other_text:
            missing.append("break_reason_other_text")

        if profile.break_started_on is None:
            missing.append("break_started_on")

        if not profile.return_date_unsure and profile.planned_return_date is None:
            missing.append("planned_return_date")

        # Include the date rule as a confirmation requirement too, even though
        # PATCH already rejects invalid date combinations.
        if (
            profile.break_started_on is not None
            and profile.planned_return_date is not None
            and profile.planned_return_date < profile.break_started_on
        ):
            missing.append("valid_break_dates")

        return missing

    def _clean_custom_list(self, values: list[str]) -> list[str]:
        """Trim, remove blanks, and de-duplicate custom user-entered labels."""
        cleaned: list[str] = []
        seen: set[str] = set()

        for value in values:
            label = value.strip()
            key = label.casefold()
            if label and key not in seen:
                cleaned.append(label)
                seen.add(key)

        return cleaned

    def _calculate_break_duration_months(self, profile: Profile) -> int | None:
        """Calculate whole calendar months between break start and return date."""
        if profile.break_started_on is None:
            return None

        end_date = profile.planned_return_date
        if end_date is None and profile.return_date_unsure:
            end_date = datetime.now(timezone.utc).date()
        if end_date is None:
            return None

        months = (end_date.year - profile.break_started_on.year) * 12
        months += end_date.month - profile.break_started_on.month

        # Do not count the current month until the day-of-month has been reached.
        if end_date.day < profile.break_started_on.day:
            months -= 1

        return max(months, 0)
