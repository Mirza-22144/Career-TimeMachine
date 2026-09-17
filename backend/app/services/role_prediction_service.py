import logging
from typing import Protocol

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.role_prediction import PredictedRoleResponse

logger = logging.getLogger(__name__)

OTHER_ROLE_ID = "other"


class RolePredictor(Protocol):
    """What the service needs from a predictor. Lets tests substitute a
    fake predictor without loading the real 13MB model bundle."""

    def predict(self, payload: dict) -> dict: ...


class RolePredictionService:
    """Predicts one future role from the confirmed profile's previous role
    and skills (AI 2.3 - serving and guardrails).

    Guardrails: the request sent to the model carries only role and skill
    labels - no token, break, custom-responsibility or other free text ever
    reaches it (matching the same minimisation ScenarioRequest already
    applies to workplace scenarios). The model's raw output is re-validated
    against PredictedRoleResponse, and a result matching "other" or the
    user's own current role is treated as a model bug, not served - the
    underlying model already excludes both by construction, so this is a
    backstop, not the primary control. Nothing about the call - success or
    failure - is logged with skill or profile content.
    """

    def __init__(
        self,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        predictor: RolePredictor | None,
    ) -> None:
        self.profiles = profiles
        self.catalogue = catalogue
        self.predictor = predictor

    def predict_for_session(self, session_token: str) -> PredictedRoleResponse:
        if self.predictor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ROLE_PREDICTION_UNAVAILABLE",
                    "message": "Role prediction is temporarily unavailable. Please try again later.",
                },
            )

        profile = self.profiles.get_by_session_token(session_token)
        if profile is None or not profile.confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROFILE_NOT_CONFIRMED",
                    "message": "Confirm the career profile before requesting a role prediction",
                },
            )
        if profile.role_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROFILE_ROLE_REQUIRED",
                    "message": "Select a previous role before requesting a role prediction",
                },
            )

        role_labels = {item.id: item.label for item in self.catalogue.get_items("roles")}
        current_label = (
            profile.role_other_text
            if profile.role_id == OTHER_ROLE_ID and profile.role_other_text
            else role_labels.get(profile.role_id, profile.role_id)
        )

        skill_labels = {item.id: item.label for item in self.catalogue.get_items("skills")}
        payload = {
            "role": {"id": profile.role_id, "label": current_label},
            "skills": {
                "catalogue": [
                    {"id": skill_id, "label": skill_labels[skill_id]}
                    for skill_id in profile.skill_ids
                    if skill_id in skill_labels
                ],
                "custom": list(profile.custom_skills),
            },
        }

        try:
            raw_prediction = self.predictor.predict(payload)
        except ValueError:
            # Unknown role id - shouldn't happen for a confirmed profile
            # whose role_id already passed catalogue validation, but the
            # model's own role set can legitimately differ from the current
            # catalogue, so this is treated as a client-visible gap, not a
            # crash.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ROLE_PREDICTION_UNSUPPORTED_ROLE",
                    "message": "Role prediction is not available for the selected previous role",
                },
            ) from None

        try:
            prediction = PredictedRoleResponse.model_validate(raw_prediction)
        except ValidationError:
            logger.error("Role prediction returned output that failed validation")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ROLE_PREDICTION_UNAVAILABLE",
                    "message": "Role prediction is temporarily unavailable. Please try again later.",
                },
            ) from None

        if prediction.predicted_role.id in {OTHER_ROLE_ID, profile.role_id}:
            # The model already excludes both by construction; this only
            # fires if that guarantee is ever broken, so fail safe rather
            # than serve a nonsensical prediction.
            logger.error("Role prediction returned an excluded role id")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ROLE_PREDICTION_UNAVAILABLE",
                    "message": "Role prediction is temporarily unavailable. Please try again later.",
                },
            )

        return prediction
