"""Boundary between the backend and whatever predicts two future IT roles
(Iteration 3, BE 3.4 - the AI team's Version 2 recommender, AI 3.2).

A separate interface from role_prediction_provider.py on purpose: the
existing GET /predicted-role (singular) is still live and used by the
current frontend, and its RolePredictionProvider contract (one role) stays
untouched so that endpoint keeps working unchanged until the frontend
switches over (FE 3.5). This is the new, additive GET /predicted-roles
(plural) contract - reuses RolePredictionRequest/SkillContext as-is, since
the request shape is identical, only the response differs.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.providers.role_prediction_provider import PredictedRoleContent, RolePredictionRequest

PREDICTED_ROLE_COUNT = 2


class TwoRolePredictionProviderError(Exception):
    """Raised by a provider that cannot supply two predictions."""


class PredictedRolesContent(BaseModel):
    """Two validated, distinct predicted roles returned by a provider."""

    model_config = ConfigDict(extra="forbid")

    predicted_roles: list[PredictedRoleContent] = Field(
        min_length=PREDICTED_ROLE_COUNT, max_length=PREDICTED_ROLE_COUNT
    )

    @model_validator(mode="after")
    def _check_distinct(self) -> "PredictedRolesContent":
        role_ids = [role.role_id for role in self.predicted_roles]
        if len(set(role_ids)) != len(role_ids):
            raise ValueError("predicted roles must be distinct")
        return self


class TwoRolePredictionProvider(ABC):
    """Predicts two future IT roles from a previous role and skills.

    Implementations return plain data (for example parsed model output);
    the backend validates it with PredictedRolesContent. Raise
    TwoRolePredictionProviderError when fewer than two predictions can be
    produced.
    """

    @abstractmethod
    def predict(self, request: RolePredictionRequest) -> dict[str, Any]:
        """Return two predicted roles matching PredictedRolesContent."""
        raise NotImplementedError
