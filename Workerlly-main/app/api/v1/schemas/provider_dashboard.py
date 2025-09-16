# File: app/api/v1/schemas/provider_dashboard.py

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class TimeFilter(str, Enum):
    today = "Today"
    this_week = "This Week"
    this_month = "This Month"
    last_month = "Last Month"
    this_year = "This Year"
    all_time = "All Time"

    def __str__(self) -> str:
        return self.value


class JobStatus(str, Enum):
    pending = "pending"
    ongoing = "ongoing"
    reached = "reached"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"


class ProviderDashboardStats(BaseModel):
    jobs_posted: int
    jobs_cancelled: int
    jobs_rejected: int
    jobs_completed: int
    total_spent: float


class RecentWork(BaseModel):
    job_id: str
    title: str
    status: JobStatus
    amount: float
    created_at: datetime


class ProviderDashboard(BaseModel):
    stats: ProviderDashboardStats
    recent_works: List[RecentWork]


class FilteredProviderDashboard(ProviderDashboard):
    time_period: TimeFilter
    job_status: Optional[JobStatus]
