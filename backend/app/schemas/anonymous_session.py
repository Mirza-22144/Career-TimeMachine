from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnonSessionResponse(BaseModel):
    """API shape for an anonymous session, returned after starting or
    checking a session."""

    # from_attributes lets Pydantic build this model by reading the
    # attributes off the AnonSession dataclass (token, created_at, ...).
    model_config = ConfigDict(from_attributes=True)

    token: str
    created_at: datetime
    last_seen_at: datetime