from datetime import date, datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class UserStatus(BaseModel):
    current_status: Optional[str] = None
    reason: Optional[str] = None
    current_job_id: Optional[str] = None
    status_updated_at: Optional[datetime] = None


class Location(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProviderProfileComplete(BaseModel):
    name: str
    city_id: str


class ProfileComplete(BaseModel):
    name: str
    category_id: str
    sub_category_id: List[str]
    city_id: str
    experience: int
    aadhar: int


class PersonalInfoUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    dob: Optional[date] = None
    marital_status: Optional[str] = Field(None, max_length=20)
    religion: Optional[str] = Field(None, max_length=50)
    diet: Optional[str] = Field(None, max_length=50)
    profile_image: Optional[str] = Field(None)


# Schema for personal information
class PersonalInfo(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = Field(None, max_length=10)
    dob: Optional[date] = None
    marital_status: Optional[str] = Field(None, max_length=20)
    religion: Optional[str] = Field(None, max_length=50)
    diet: Optional[str] = Field(None, max_length=50)
    profile_image: Optional[str] = Field(default=None)

    @field_validator("profile_image")
    def set_profile_image(cls, v: Optional[str]) -> str:
        return v or "public/profiles/default.png"


# Schema for provider-specific stats
class ProviderStats(BaseModel):
    city_id: Optional[str] = None  # Expecting a string
    city_name: Optional[str] = None
    # total_jobs_posted: Optional[int] = 0
    # total_jobs_completed: Optional[int] = 0
    # total_jobs_cancelled: Optional[int] = 0
    # total_spent: Optional[float] = 0.0
    # total_reviews: Optional[int] = 0
    # avg_rating: Optional[float] = 0.0
    # sum_ratings: Optional[int] = 0


# Schema for the provider profile response
class ProviderProfileResponse(BaseModel):
    user_id: str = Field(..., alias="user_id")
    mobile: str
    personal_info: PersonalInfo
    provider_stats: ProviderStats
    job_id: Optional[str]  # Add this line to include job_id

    # Schema for seeker-specific stats


class SeekerStats(BaseModel):
    wallet_balance: Optional[float] = 0.0
    city_id: Optional[str] = None
    city_name: Optional[str] = None
    category: Optional[Dict[str, Any]] = None
    location: Location
    experience: Optional[int] = 0
    user_status: Optional[Dict[str, Any]] = None
    # total_jobs_done: Optional[int] = 0
    # total_earned: Optional[float] = 0.0
    # total_hours_worked: Optional[int] = 0
    # total_reviews: Optional[int] = 0
    # avg_rating: Optional[float] = 0.0
    # sum_ratings: Optional[int] = 0

    # Schema for the seeker profile response


class SeekerProfileResponse(BaseModel):
    user_id: str = Field(..., alias="user_id")
    mobile: str
    personal_info: PersonalInfo
    seeker_stats: SeekerStats

    class Config:
        from_attributes = True
        allow_population_by_name = True
