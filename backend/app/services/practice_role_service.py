import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.repositories.interfaces.role_choice_repository import RoleChoiceRepository
from app.schemas.practice_role import PracticeRoleUpdate

logger = logging.getLogger(__name__)

PREVIOUS_ROLE = "previous"
PREDICTED_ROLE = "predicted"
OTHER_ROLE_ID = "other"


@dataclass
class PracticeRoleSelection:
    """The role chosen for workplace practice and whether it is the user's
    previous role or a predicted one. All fields are None when nothing is
    selected."""

    role_id: str | None
    role_label: str | None
    source: str | None


@dataclass
class PracticeContext:
    """Career context handed to workplace practice.

    Holds only what a scenario needs: skills and role (Iteration 3 rule,
    BE 3.1). The token, break dates, break reason, years of experience,
    responsibilities and custom free-text skills/responsibilities are
    deliberately left out so they never reach a scenario provider - years of
    experience and responsibilities are used for job-description comparison
    only, not scenario generation.
    """

    role_id: str
    role_label: str
    role_source: str
    skills: list[str]


class PracticeRoleService:
    """Business logic for the role selected on Your Direction and the career
    context that workplace practice builds on."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        role_choices: RoleChoiceRepository | None = None,
    ) -> None:
        # Depend on interfaces so storage and catalogue data can be swapped.
        self.profiles = profiles
        self.catalogue = catalogue
        # Optional: the dated history of chosen roles (AC 3.4.1).
        self.role_choices = role_choices

    def get_for_session(self, session_token: str) -> PracticeRoleSelection:
        """Return the saved practice role for the session, if any."""
        return self._selection(self.profiles.get_by_session_token(session_token))

    def get_for_profile(self, profile: Profile | None) -> PracticeRoleSelection:
        """Same as get_for_session for an already-loaded profile."""
        return self._selection(profile)

    def select_for_session(
        self,
        session_token: str,
        update: PracticeRoleUpdate,
    ) -> PracticeRoleSelection:
        """Validate and save the chosen practice role."""
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None:
            profile = Profile(session_token=session_token)

        role_labels = self._role_labels()
        if update.role_id not in role_labels:
            self._reject(f"Invalid role_id: {update.role_id}")

        if update.source == PREVIOUS_ROLE and update.role_id != profile.role_id:
            self._reject("role_id must match the saved previous role")

        # "Other" is a free-text previous role, never a prediction.
        if update.source == PREDICTED_ROLE and update.role_id == OTHER_ROLE_ID:
            self._reject(f"Invalid role_id: {update.role_id}")

        saved = self.profiles.save(
            replace(
                profile,
                practice_role_id=update.role_id,
                practice_role_source=update.source,
            )
        )
        self._record_choice(session_token, update.role_id)
        return self._selection(saved, role_labels)

    def _record_choice(self, session_token: str, role_id: str) -> None:
        """Add the role to her dated history. Best effort: the choice itself
        is already saved on the profile, so a history failure (for example
        the role_choice table not created yet) must not fail the request."""
        if self.role_choices is None:
            return
        try:
            self.role_choices.record(session_token, role_id, datetime.now(timezone.utc))
        except Exception:
            logger.warning("Could not record role choice history", exc_info=True)

    def build_practice_context(self, session_token: str) -> PracticeContext:
        """Return the saved career context for practice, so the user never has
        to re-enter it. Fails clearly when the profile or role is missing."""
        profile = self.profiles.get_by_session_token(session_token)
        if profile is None or not profile.confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROFILE_NOT_CONFIRMED",
                    "message": "Confirm the career profile before starting practice",
                },
            )

        selection = self._selection(profile)
        if selection.role_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PRACTICE_ROLE_REQUIRED",
                    "message": "Select a practice role before starting practice",
                },
            )

        return PracticeContext(
            role_id=selection.role_id,
            role_label=selection.role_label,
            role_source=selection.source,
            skills=self._labels("skills", profile.skill_ids),
        )

    def _selection(
        self,
        profile: Profile | None,
        role_labels: dict[str, str] | None = None,
    ) -> PracticeRoleSelection:
        """Resolve the stored selection into id, label and source."""
        if profile is None or profile.practice_role_id is None:
            return PracticeRoleSelection(role_id=None, role_label=None, source=None)

        # A "previous" choice only stands while it still matches the saved
        # previous role; editing Your Story means choosing again.
        if (
            profile.practice_role_source == PREVIOUS_ROLE
            and profile.practice_role_id != profile.role_id
        ):
            return PracticeRoleSelection(role_id=None, role_label=None, source=None)

        labels = role_labels if role_labels is not None else self._role_labels()
        if profile.practice_role_id not in labels:
            return PracticeRoleSelection(role_id=None, role_label=None, source=None)

        label = labels[profile.practice_role_id]
        if profile.practice_role_id == OTHER_ROLE_ID and profile.role_other_text:
            label = profile.role_other_text

        return PracticeRoleSelection(
            role_id=profile.practice_role_id,
            role_label=label,
            source=profile.practice_role_source,
        )

    def _role_labels(self) -> dict[str, str]:
        return {item.id: item.label for item in self.catalogue.get_items("roles")}

    def _labels(self, catalogue_kind: str, item_ids: list[str]) -> list[str]:
        """Resolve catalogue IDs to labels, skipping any that no longer exist."""
        labels = {item.id: item.label for item in self.catalogue.get_items(catalogue_kind)}
        return [labels[item_id] for item_id in item_ids if item_id in labels]

    def _reject(self, message: str) -> None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
