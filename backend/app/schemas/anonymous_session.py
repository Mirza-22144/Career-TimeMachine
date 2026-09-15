from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnonSessionResponse(BaseModel):
    """API shape returned once, when a session is started. This is the only
    response that ever includes the raw access token."""

    # from_attributes lets Pydantic build this model by reading the
    # attributes off the IssuedSession dataclass (token, created_at, ...).
    model_config = ConfigDict(from_attributes=True)

    token: str
    created_at: datetime
    last_seen_at: datetime


class AnonSessionStatusResponse(BaseModel):
    """API shape for checking an existing token. Confirms the token is valid
    without echoing it back."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    last_seen_at: datetime
