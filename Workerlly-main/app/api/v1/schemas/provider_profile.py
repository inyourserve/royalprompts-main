from datetime import datetime
from typing import List

from pydantic import BaseModel


class RatingBreakdown(BaseModel):
    five_star: int
    four_star: int
    three_star: int
    two_star: int
    one_star: int


class Review(BaseModel):
    seeker_name: str
    date: datetime
    feedback: str
    rating: int


class ProviderProfile(BaseModel):
    id: str
    name: str
    profile_picture: str
    total_works: int
    average_rating: float
    total_ratings: int
    total_spent: float  # This is actually "total earned" for providers
    rating_breakdown: RatingBreakdown
    reviews: List[Review]
