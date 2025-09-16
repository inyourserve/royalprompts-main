from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class JobSeekerView(BaseModel):
    id: str
    title: str
    description: str
    hourly_rate: float
    city: str
    provider_name: str
    created_at: datetime


class JobSeekerListResponse(BaseModel):
    jobs: List[JobSeekerView]
    total: int
    page: int
    page_size: int


class JobListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"
    min_hourly_rate: Optional[float] = None
    max_hourly_rate: Optional[float] = None


class UserProfile(BaseModel):
    id: str
    category_id: str
    city_id: str
