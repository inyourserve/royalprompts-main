import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.seeker_dashboard import (
    SeekerDashboard,
    SeekerDashboardStats,
    RecentCompletedJob,
    FilteredSeekerDashboard,
)
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()
logger = logging.getLogger(__name__)


class TimeFilter(str, Enum):
    today = "today"
    this_week = "this_week"
    this_month = "this_month"
    last_month = "last_month"
    this_year = "this_year"
    all_time = "all_time"


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
    "/seeker-dashboard",
    response_model=SeekerDashboard,
    dependencies=[Depends(role_required("seeker"))],
)
async def get_seeker_dashboard_quick_view(
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = ObjectId(current_user["user_id"])

        # Get user stats
        user_stats_doc = await motor_db.user_stats.find_one({"user_id": user_id})
        if not user_stats_doc:
            raise HTTPException(status_code=404, detail="User stats not found")

        user_stats = extract_user_stats(user_stats_doc)
        seeker_stats = user_stats.get("seeker_stats", {})

        # Get recent completed jobs where the current user is assigned as the provider
        recent_jobs = (
            await motor_db.jobs.find({"assigned_to": user_id, "status": "completed"})
            .sort("created_at", -1)
            .limit(5)
            .to_list(length=None)
        )

        return SeekerDashboard(
            stats=SeekerDashboardStats(
                avg_rating_as_seeker=seeker_stats.get("avg_rating", 0),
                total_jobs_done=seeker_stats.get("total_jobs_done", 0),
                total_hours_worked=seeker_stats.get("total_hours_worked", 0),
                total_earned=seeker_stats.get("total_earned", 0),
            ),
            recent_jobs=[
                RecentCompletedJob(
                    job_id=str(job["_id"]),
                    title=job.get("title", "Untitled Job"),
                    billable_hours=job.get("billable_hours", 0),
                    total_amount=job.get("total_amount", 0),
                    created_at=job.get("created_at"),
                )
                for job in recent_jobs
            ],
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching seeker dashboard quick view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the dashboard data",
        )


@router.get(
    "/seeker-dashboard/filtered",
    response_model=FilteredSeekerDashboard,
    dependencies=[Depends(role_required("seeker"))],
)
async def get_seeker_dashboard_filtered_view(
    current_user: dict = Depends(get_current_user),
    time_filter: TimeFilter = Query(
        TimeFilter.all_time, description="Time filter for dashboard statistics"
    ),
):
    try:
        user_id = ObjectId(current_user["user_id"])
        start_date, end_date = get_date_range(time_filter)

        # Jobs aggregation pipeline
        jobs_pipeline = [
            {
                "$match": {
                    "assigned_to": user_id,
                    "status": "completed",
                    "created_at": {"$gte": start_date, "$lte": end_date},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_jobs_done": {"$sum": 1},
                    "total_earned": {"$sum": "$total_amount"},
                    "total_hours": {"$sum": "$billable_hours"},
                    "recent_jobs": {
                        "$push": {
                            "_id": "$_id",
                            "title": "$title",
                            "billable_hours": "$billable_hours",
                            "total_amount": "$total_amount",
                            "created_at": "$created_at",
                        }
                    },
                }
            },
            {
                "$project": {
                    "total_jobs_done": 1,
                    "total_earned": 1,
                    "total_hours": 1,
                    "recent_jobs": {"$slice": ["$recent_jobs", 5]},
                }
            },
        ]

        # Reviews aggregation pipeline
        reviews_pipeline = [
            {
                "$match": {
                    "reviewee_id": user_id,
                    "reviewer_role": "provider",
                    "created_at": {"$gte": start_date, "$lte": end_date},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "sum_ratings": {"$sum": "$rating"},
                    "count_ratings": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "avg_rating": {
                        "$cond": [
                            {"$eq": ["$count_ratings", 0]},
                            0,
                            {"$divide": ["$sum_ratings", "$count_ratings"]},
                        ]
                    }
                }
            },
        ]

        # Execute both pipelines concurrently
        jobs_result, reviews_result = await asyncio.gather(
            motor_db.jobs.aggregate(jobs_pipeline).to_list(length=1),
            motor_db.reviews.aggregate(reviews_pipeline).to_list(length=1),
        )

        jobs_stats = jobs_result[0] if jobs_result else {}
        reviews_stats = reviews_result[0] if reviews_result else {}

        return FilteredSeekerDashboard(
            time_period=time_filter,
            stats=SeekerDashboardStats(
                avg_rating_as_seeker=reviews_stats.get("avg_rating", 0),
                total_jobs_done=jobs_stats.get("total_jobs_done", 0),
                total_hours_worked=jobs_stats.get("billable_hours", 0),
                total_earned=jobs_stats.get("total_earned", 0),
            ),
            recent_jobs=[
                RecentCompletedJob(
                    job_id=str(job["_id"]),
                    title=job.get("title", "Untitled Job"),
                    billable_hours=job.get("billable_hours", 0),
                    total_amount=job.get("total_amount", 0),
                    created_at=job.get("created_at"),
                )
                for job in jobs_stats.get("recent_jobs", [])
            ],
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching seeker dashboard filtered view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the filtered dashboard data",
        )
