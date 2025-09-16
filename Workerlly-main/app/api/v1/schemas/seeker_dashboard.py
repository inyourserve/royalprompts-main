from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


class TimeFilter(str, Enum):
    today = "today"
    this_week = "this_week"
    this_month = "this_month"
    last_month = "last_month"
    this_year = "this_year"
    all_time = "all_time"


class SeekerDashboardStats(BaseModel):
    avg_rating_as_seeker: float
    total_jobs_done: int
    total_hours_worked: int
    total_earned: float


class RecentCompletedJob(BaseModel):
    job_id: str
    title: str
    billable_hours: int
    total_amount: float
    created_at: datetime


class SeekerDashboard(BaseModel):
    stats: SeekerDashboardStats
    recent_jobs: List[RecentCompletedJob]


class FilteredSeekerDashboard(SeekerDashboard):
    time_period: TimeFilter
