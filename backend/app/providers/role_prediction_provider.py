"""Boundary between the backend and whatever predicts a future IT role.

The AI/data-science owner provides the production implementation (model,
training, evaluation). The backend depends only on this interface and
validates everything a provider returns with PredictedRoleContent below, so
a provider cannot push unexpected fields through to the user.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

RoleId = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
RoleLabel = Field(min_length=1, max_length=120)


class RolePredictionProviderError(Exception):
    """Raised by a provider that cannot supply a prediction."""


@dataclass(frozen=True)
class SkillContext:
    """One skill available to the predictor, catalogue or free-text."""

    id: str | None
    label: str


@dataclass(frozen=True)
class RolePredictionRequest:
    """Input for one role prediction.

    Career context only: no token, profile or session identifiers. skills
    covers both catalogue selections (id + label) and free-text custom
    skills (label only, id is None).
    """

    role_id: str
    role_label: str
    skills: tuple[SkillContext, ...]


class PredictedRoleContent(BaseModel):
    """A validated predicted role returned by a provider."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = RoleId
    role_label: str = RoleLabel


class RolePredictionProvider(ABC):
    """Predicts one future IT role from a previous role and skills.

    Implementations return plain data (for example parsed model output);
    the backend validates it with PredictedRoleContent. Raise
    RolePredictionProviderError when no prediction can be produced.
    """

    @abstractmethod
    def predict(self, request: RolePredictionRequest) -> dict[str, Any]:
        """Return one predicted role matching PredictedRoleContent."""
        raise NotImplementedError
