from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnonSessionResponse(BaseModel):
    # from_attributes lets Pydantic build this model by reading the
    # attributes off our AnonSession dataclass (token, created_at, ...).
    model_config = ConfigDict(from_attributes=True)

    token: str
    created_at: datetime
    last_seen_at: datetime