from dataclasses import dataclass, replace

from fastapi import HTTPException, status

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.schemas.practice_role import PracticeRoleUpdate

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

    Holds only what a scenario needs. The token, break dates, break reason
    and custom free-text skills/responsibilities are deliberately left out so
    they never reach a scenario provider.
    """

    role_id: str
    role_label: str
    role_source: str
    years_experience: str | None
    skills: list[str]
    responsibilities: list[str]


class PracticeRoleService:
    """Business logic for the role selected on Your Direction and the career
    context that workplace practice builds on."""

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
    ) -> None:
        # Depend on interfaces so storage and catalogue data can be swapped.
        self.profiles = profiles
        self.catalogue = catalogue

    def get_for_session(self, session_token: str) -> PracticeRoleSelection:
        """Return the saved practice role for the session, if any."""
        return self._selection(self.profiles.get_by_session_token(session_token))

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
        return self._selection(saved, role_labels)

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
            years_experience=self._label("experience-options", profile.years_experience),
            skills=self._labels("skills", profile.skill_ids),
            responsibilities=self._labels("responsibilities", profile.responsibility_ids),
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

    def _label(self, catalogue_kind: str, item_id: str | None) -> str | None:
        """Resolve one optional catalogue ID to its label."""
        labels = self._labels(catalogue_kind, [item_id]) if item_id else []
        return labels[0] if labels else None

    def _labels(self, catalogue_kind: str, item_ids: list[str]) -> list[str]:
        """Resolve catalogue IDs to labels, skipping any that no longer exist."""
        labels = {item.id: item.label for item in self.catalogue.get_items(catalogue_kind)}
        return [labels[item_id] for item_id in item_ids if item_id in labels]

    def _reject(self, message: str) -> None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
