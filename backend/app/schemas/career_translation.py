from pydantic import BaseModel, ConfigDict


class NamedItemResponse(BaseModel):
    """API shape for an item displayed as id + name."""

    # Lets Pydantic read from the service dataclasses.
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class SkillTranslationResponse(BaseModel):
    """Career-area connections for one selected previous skill."""

    # Lets Pydantic read nested dataclasses returned by the service.
    model_config = ConfigDict(from_attributes=True)

    previous_skill: NamedItemResponse
    connected_areas: list[NamedItemResponse]
