
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from career_role_explainer_v1 import (
    CareerRoleExplainerV1,
)

from predictive_role_explanation_models_v1 import (
    RoleExplanation,
)


class BackendExplainedRole(BaseModel):
    """One backend-ready role recommendation."""

    model_config = ConfigDict(
        extra="forbid"
    )

    role_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9_]+$",
    )

    role_label: str = Field(
        min_length=1,
        max_length=120,
    )

    explanation: RoleExplanation


class BackendExplainedRolesResponse(BaseModel):
    """Exactly two backend-ready recommendations."""

    model_config = ConfigDict(
        extra="forbid"
    )

    predicted_roles: list[
        BackendExplainedRole
    ] = Field(
        min_length=2,
        max_length=2,
    )


    @model_validator(mode="after")
    def validate_distinct_roles(self):
        role_ids = [
            role.role_id
            for role in self.predicted_roles
        ]

        if len(set(role_ids)) != 2:
            raise ValueError(
                "The two backend role IDs "
                "must be distinct."
            )

        return self


class ExplainedRolePredictionProviderV1:
    """Backend-facing adapter for explained predictions."""

    def __init__(self, bundle_path):
        self.explainer = CareerRoleExplainerV1(
            bundle_path
        )


    def predict(
        self,
        payload: dict[str, Any],
    ):
        explained_response = (
            self.explainer.predict(
                payload
            )
        )

        backend_response = {
            "predicted_roles": [
                {
                    "role_id": role["id"],
                    "role_label": (
                        role["label"]
                    ),
                    "explanation": (
                        role["explanation"]
                    ),
                }
                for role in explained_response[
                    "predicted_roles"
                ]
            ]
        }

        validated = (
            BackendExplainedRolesResponse
            .model_validate(
                backend_response
            )
        )

        return validated.model_dump(
            mode="json"
        )
