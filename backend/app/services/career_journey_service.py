from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import ProfileRepository


@dataclass
class CatalogueSelection:
    """Internal labelled catalogue selection used in journey responses."""

    id: str
    label: str


@dataclass
class CareerBreakSummary:
    """Internal career break timing summary built from the profile."""

    break_started_on: date | None
    planned_return_date: date | None
    return_date_unsure: bool
    break_duration_months: int | None


@dataclass
class SelectedSkillsSummary:
    """Internal selected-skills summary with resolved catalogue labels."""

    catalogue_skills: list[CatalogueSelection]
    custom_skills: list[str]


@dataclass
class CareerJourney:
    """Internal career journey summary returned by the service."""

    previous_role: CatalogueSelection | None
    years_experience: CatalogueSelection | None
    career_break: CareerBreakSummary
    current_return_status: CatalogueSelection | None
    selected_skills: SelectedSkillsSummary
    strengths: list[str]


class CareerJourneyService:
    """Business logic for building the confirmed profile journey summary."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
    ) -> None:
        # Depend on interfaces so the later database swap stays isolated.
        self.profiles = profiles
        self.catalogue = catalogue

    def build_for_session(self, session_token: str) -> CareerJourney:
        """Build a structured journey from the current session's profile."""
        profile = self.profiles.get_by_session_token(session_token)

        # A journey is only meaningful after the user confirms their profile.
        if profile is None or not profile.confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="profile not confirmed",
            )

        # Phase 13 will add return_readiness to Profile. getattr keeps this
        # Phase 11 endpoint returning null until that field exists and is set.
        return_readiness = getattr(profile, "return_readiness", None)

        return CareerJourney(
            previous_role=self._selection_or_none("roles", profile.role_id),
            years_experience=self._selection_or_none(
                "experience-options",
                profile.years_experience,
            ),
            career_break=CareerBreakSummary(
                break_started_on=profile.break_started_on,
                planned_return_date=profile.planned_return_date,
                return_date_unsure=profile.return_date_unsure,
                break_duration_months=profile.break_duration_months,
            ),
            current_return_status=self._selection_or_none(
                "return-statuses",
                return_readiness,
            ),
            selected_skills=SelectedSkillsSummary(
                catalogue_skills=[
                    self._required_selection("skills", skill_id)
                    for skill_id in profile.skill_ids
                ],
                custom_skills=profile.custom_skills,
            ),
            # Iteration 1 never infers strengths. Keep this explicitly empty.
            strengths=[],
        )

    def _selection_or_none(
        self,
        catalogue_kind: str,
        item_id: str | None,
    ) -> CatalogueSelection | None:
        """Resolve an optional catalogue ID into id + label."""
        if item_id is None:
            return None
        return self._required_selection(catalogue_kind, item_id)

    def _required_selection(
        self,
        catalogue_kind: str,
        item_id: str,
    ) -> CatalogueSelection:
        """Resolve a required catalogue ID, failing if data is inconsistent."""
        labels_by_id = {
            item.id: item.label
            for item in self.catalogue.get_items(catalogue_kind)
        }

        if item_id not in labels_by_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Missing catalogue label for {catalogue_kind}: {item_id}",
            )

        return CatalogueSelection(id=item_id, label=labels_by_id[item_id])
