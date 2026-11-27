from pydantic import BaseModel, ConfigDict


class CareerDirectionUpdate(BaseModel):
    """PATCH body for saving career-direction selections.

    Both fields are optional so the frontend can save one control at a time.
    Sending null clears the saved selection.
    """

    return_readiness: str | None = None
    area_to_explore: str | None = None


class CareerDirectionResponse(BaseModel):
    """Current career-direction selections stored on the profile."""

    # Lets Pydantic read from the service dataclass.
    model_config = ConfigDict(from_attributes=True)

    return_readiness: str | None
    area_to_explore: str | None
