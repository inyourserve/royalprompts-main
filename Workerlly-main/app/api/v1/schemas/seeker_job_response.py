from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Provider(BaseModel):
    id: str
    name: str
    mobile: Optional[int] = None
    profile_image: str
    avg_rating: float


class JobSummary(BaseModel):
    title: str
    description: str
    current_rate: float
    booking_time: datetime
    updated_at: datetime


class AddressSnapshot(BaseModel):
    _id: str
    city_id: str
    address_line1: str
    apartment_number: Optional[str] = None
    landmark: Optional[str] = None
    label: str
    latitude: float
    longitude: float
    location: dict = Field(..., example={"type": "Point", "coordinates": [0.0, 0.0]})


class JobMeta(BaseModel):
    status: str
    is_reached: Optional[bool] = False
    estimated_time: Optional[int] = None
    reaching_time: Optional[datetime] = None
    job_started_at: Optional[datetime] = None
    job_done_at: Optional[datetime] = None
    total_hours_worked: Optional[str] = None
    total_amount: Optional[float] = None
    paid: bool = False
    payment_method: Optional[str] = None
    reason: Optional[str] = None


class WorkCategory(BaseModel):
    category_name: str
    category_thumbnail: str
    subcategory_name: List[str]
    subcategory_thumbnail: List[str]


class SeekerReview(BaseModel):
    review_done: bool = False
    review_id: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ProviderReview(BaseModel):
    review_done: bool = False
    review_id: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class JobResponse(BaseModel):
    _id: str
    provider: Provider
    job_summary: JobSummary
    address: AddressSnapshot
    job_meta: JobMeta
    work_category: WorkCategory
    seeker_review: SeekerReview
    provider_review: ProviderReview

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
