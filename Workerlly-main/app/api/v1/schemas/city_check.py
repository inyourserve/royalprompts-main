from pydantic import BaseModel


class CityCheckRequest(BaseModel):
    city_id: str


class CityCheckResponse(BaseModel):
    is_served: bool


class CityCreateRequest(BaseModel):
    name: str
    is_served: bool
