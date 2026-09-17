from pydantic import BaseModel, ConfigDict, Field


class CareerDirectionUpdate(BaseModel):
    """PATCH body for saving career-direction selections.

    Both fields are optional so the frontend can save one control at a time.
    Sending null clears the saved selection.
    """

    model_config = ConfigDict(extra="forbid")

    # Catalogue ids (VARCHAR(64)); unknown ids are still rejected by the service.
    return_readiness: str | None = Field(default=None, max_length=64)
    area_to_explore: str | None = Field(default=None, max_length=64)


class CareerDirectionResponse(BaseModel):
    """Current career-direction selections stored on the profile."""

    # Lets Pydantic read from the service dataclass.
    model_config = ConfigDict(from_attributes=True)

    return_readiness: str | None
    area_to_explore: str | None
