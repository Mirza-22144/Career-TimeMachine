from pydantic import BaseModel, ConfigDict


class CatalogueItemResponse(BaseModel):
    """API shape for one option in a catalogue list, such as a role or skill."""

    model_config = ConfigDict(from_attributes=True)  # read CatalogueItem dataclass
    id: str
    label: str
    in_demand: bool = False
    hot_technology: bool = False
