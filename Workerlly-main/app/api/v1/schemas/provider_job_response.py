from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Seeker(BaseModel):
    id: str
    name: str
    mobile: Optional[int] = None
    profile_image: str
    category: str
    avg_rating: float


class JobSummary(BaseModel):
    title: str
    description: str
    current_rate: float
    booking_time: Optional[datetime] = None


class JobMeta(BaseModel):
    status: str
    is_reached: Optional[bool] = False
    work_category: str
    estimated_time: Optional[int] = None
    job_booking_time: Optional[datetime] = None
    reaching_time: Optional[datetime] = None
    job_start_otp: Optional[int] = None
    job_start_otp_verified: Optional[bool] = None
    job_started_at: Optional[datetime] = None
    job_done_otp: Optional[int] = None
    job_done_otp_verified: Optional[bool] = None
    job_done_at: Optional[datetime] = None
    total_hours_worked: Optional[str] = None
    total_amount: Optional[float] = None
    paid: bool = False
    reason: Optional[str] = None


class ProviderReview(BaseModel):
    review_done: bool = False
    review_id: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class SeekerReview(BaseModel):
    review_done: bool = False
    review_id: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ProviderJobResponse(BaseModel):
    _id: str
    seeker: Seeker
    job_summary: JobSummary
    job_meta: JobMeta
    provider_review: ProviderReview
    seeker_review: SeekerReview

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
