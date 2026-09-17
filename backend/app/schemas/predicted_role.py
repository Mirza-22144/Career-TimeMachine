from pydantic import BaseModel, ConfigDict


class PredictedRoleResponse(BaseModel):
    """The AI-predicted future role for the session's previous role and
    skills. Both fields are null when no prediction is available (no
    previous role saved yet, or the model could not produce one)."""

    model_config = ConfigDict(from_attributes=True)

    role_id: str | None
    role_label: str | None
