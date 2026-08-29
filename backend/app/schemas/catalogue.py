



from pydantic import BaseModel, ConfigDict


class CatalogueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # read CatalogueItem dataclass
    id: str
    label: str
