from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PracticeRoleSource = Literal["previous", "predicted"]


class PracticeRoleUpdate(BaseModel):
    """PUT body for the role chosen on Your Direction."""

    # New Iteration 2 request bodies reject unexpected fields.
    model_config = ConfigDict(extra="forbid")

    # Matches the role catalogue's ids (see data/seed/seed_roles.sql).
    role_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    source: PracticeRoleSource


class PracticeRoleResponse(BaseModel):
    """The saved practice role. Every field is null when none is selected."""

    model_config = ConfigDict(from_attributes=True)

    role_id: str | None
    role_label: str | None
    source: PracticeRoleSource | None
