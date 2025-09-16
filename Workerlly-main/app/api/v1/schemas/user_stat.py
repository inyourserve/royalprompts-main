from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserStatus(BaseModel):
    current_status: Optional[str] = "free"
    reason: Optional[str] = None
    current_job_id: Optional[str] = None
    status_updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserStats(BaseModel):
    user_id: str
    wallet_balance: float = 110.0
    total_reviews_as_seeker: int = 0
    total_reviews_as_provider: int = 0
    avg_rating_as_seeker: float = 0.0
    avg_rating_as_provider: float = 0.0
    total_jobs_posted: int = 0
    total_jobs_done: int = 0
    total_completed_jobs: int = 0
    total_spent: float = 0.0
    total_earned: float = 0.0
    user_status: UserStatus = Field(default_factory=UserStatus)
