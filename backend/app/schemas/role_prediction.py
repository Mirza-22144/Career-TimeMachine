from pydantic import BaseModel, ConfigDict


class PredictedRole(BaseModel):
    """One predicted role. Deliberately just an id and a label - no
    confidence score, probability or ranking is ever exposed."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str


class PredictedRoleResponse(BaseModel):
    """Validated output of the role-prediction model.

    Every prediction is checked against this schema before it can reach a
    response, the same guardrail this codebase already applies to workplace
    scenarios (see ScenarioContent/FeedbackContent) - the model is treated as
    a provider that must not be trusted to shape its own output, so
    extra="forbid" catches anything beyond id/label (a confidence score, for
    instance) before it ever leaves the backend.
    """

    model_config = ConfigDict(extra="forbid")

    predicted_role: PredictedRole
