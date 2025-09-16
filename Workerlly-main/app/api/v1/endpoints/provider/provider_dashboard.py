# File: app/api/v1/endpoints/provider_dashboard.py

import logging
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.provider_dashboard import (
    ProviderDashboard,
    FilteredProviderDashboard,
    ProviderDashboardStats,
    RecentWork,
    TimeFilter,
    JobStatus,
)
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()
logger = logging.getLogger(__name__)


def get_date_range(time_filter: TimeFilter):
    now = datetime.utcnow()
    if time_filter == TimeFilter.today:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif time_filter == TimeFilter.this_week:
        start_date = now - timedelta(days=now.weekday())
        end_date = start_date + timedelta(days=6)
    elif time_filter == TimeFilter.this_month:
        start_date = now.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif time_filter == TimeFilter.last_month:
        start_date = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = now.replace(day=1) - timedelta(days=1)
    elif time_filter == TimeFilter.this_year:
        start_date = now.replace(month=1, day=1)
        end_date = now.replace(month=12, day=31)
    else:  # all_time
        start_date = datetime.min
        end_date = datetime.max
    return start_date, end_date


@router.get(
    "/provider-dashboard",
    response_model=ProviderDashboard,
    dependencies=[Depends(role_required("provider"))],
)
async def get_provider_dashboard_quick_view(
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = ObjectId(current_user["user_id"])

        # Get user stats
        user_stats_doc = await motor_db.user_stats.find_one({"user_id": user_id})
        if not user_stats_doc:
            raise HTTPException(status_code=404, detail="User stats not found")

        user_stats = extract_user_stats(user_stats_doc)
        provider_stats = user_stats.get("provider_stats", {})

        # Get recent works (all job statuses)
        recent_works = (
            await motor_db.jobs.find({"user_id": user_id})
            .sort("created_at", -1)
            .to_list(length=None)
        )

        return ProviderDashboard(
            stats=ProviderDashboardStats(
                jobs_posted=provider_stats.get("total_jobs_posted", 0),
                jobs_cancelled=provider_stats.get("total_jobs_cancelled", 0),
                jobs_rejected=provider_stats.get("total_jobs_rejected", 0),
                jobs_completed=provider_stats.get("total_jobs_completed", 0),
                total_spent=provider_stats.get("total_spent", 0),
            ),
            recent_works=[
                RecentWork(
                    job_id=str(job["_id"]),
                    title=job.get("title", "Untitled Job"),
                    status=JobStatus(job.get("status")),
                    amount=job.get("total_amount", 0),
                    created_at=job.get("created_at"),
                )
                for job in recent_works
            ],
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching provider dashboard quick view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the dashboard data",
        )


@router.get(
    "/provider-dashboard/filtered",
    response_model=FilteredProviderDashboard,
    dependencies=[Depends(role_required("provider"))],
)
async def get_provider_dashboard_filtered_view(
    current_user: dict = Depends(get_current_user),
    time_filter: TimeFilter = Query(
        TimeFilter.all_time, description="Time filter for dashboard statistics"
    ),
    job_status: Optional[JobStatus] = Query(None, description="Filter by job status"),
):
    try:
        user_id = ObjectId(current_user["user_id"])
        start_date, end_date = get_date_range(time_filter)

        # Base match condition
        match_condition = {
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
        }

        # Add job status to match condition if provided
        if job_status:
            match_condition["status"] = job_status.value

        # Jobs aggregation pipeline
        jobs_pipeline = [
            {"$match": match_condition},
            {
                "$group": {
                    "_id": None,
                    "jobs_posted": {"$sum": 1},
                    "jobs_completed": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", JobStatus.completed.value]},
                                1,
                                0,
                            ]
                        }
                    },
                    "jobs_cancelled": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", JobStatus.cancelled.value]},
                                1,
                                0,
                            ]
                        }
                    },
                    "jobs_rejected": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", JobStatus.rejected.value]},
                                1,
                                0,
                            ]
                        }
                    },
                    "total_spent": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", JobStatus.completed.value]},
                                "$total_amount",
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        jobs_result = await motor_db.jobs.aggregate(jobs_pipeline).to_list(length=1)
        jobs_stats = jobs_result[0] if jobs_result else {}

        # Separate query for recent works
        recent_works = (
            await motor_db.jobs.find(match_condition)
            .sort("created_at", -1)
            .to_list(length=None)
        )

        return FilteredProviderDashboard(
            time_period=time_filter,
            job_status=job_status,
            stats=ProviderDashboardStats(
                jobs_posted=jobs_stats.get("jobs_posted", 0),
                jobs_cancelled=jobs_stats.get("jobs_cancelled", 0),
                jobs_rejected=jobs_stats.get("jobs_rejected", 0),
                jobs_completed=jobs_stats.get("jobs_completed", 0),
                total_spent=jobs_stats.get("total_spent", 0),
            ),
            recent_works=[
                RecentWork(
                    job_id=str(job["_id"]),
                    title=job.get("title", "Untitled Job"),
                    status=JobStatus(job.get("status")),
                    amount=job.get("total_amount", 0),
                    created_at=job.get("created_at"),
                )
                for job in recent_works
            ],
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching provider dashboard filtered view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the filtered dashboard data",
        )
