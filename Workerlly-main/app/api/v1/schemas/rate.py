from pydantic import BaseModel


class Rate(BaseModel):
    city_id: str
    category_id: str
    rate_per_hour: float
    min_hourly_rate: float
    max_hourly_rate: float
