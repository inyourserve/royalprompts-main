# File: app/api/v1/endpoints/seeker_job_history.py

import logging
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required

router = APIRouter()
logger = logging.getLogger(__name__)


class JobHistoryItem(BaseModel):
    id: str
    title: str
    status: str
    hourly_rate: float
    billable_hours: Optional[int] = None
    created_at: datetime


class JobHistoryResponse(BaseModel):
    cancelled: List[JobHistoryItem]
    completed: List[JobHistoryItem]
    ongoing: List[JobHistoryItem]


@router.get(
    "/jobs/history",
    response_model=JobHistoryResponse,
    dependencies=[Depends(role_required("seeker"))],
)
async def get_seeker_job_history(current_user: dict = Depends(get_current_user)):
    try:
        user_id = ObjectId(current_user["user_id"])

        async def get_jobs_by_status(status):
            jobs = (
                await motor_db.jobs.find({"assigned_to": user_id, "status": status})
                .sort("created_at", -1)
                .to_list(None)
            )

            return [
                JobHistoryItem(
                    id=str(job["_id"]),
                    title=job.get("title", "Untitled Job"),
                    status=status,
                    hourly_rate=job.get("current_rate", 0),
                    billable_hours=job.get("billable_hours", 0),
                    created_at=job.get("created_at", datetime.utcnow()),
                )
                for job in jobs
            ]

        cancelled_jobs = await get_jobs_by_status("cancelled")
        completed_jobs = await get_jobs_by_status("completed")
        ongoing_jobs = await get_jobs_by_status("ongoing")

        return JobHistoryResponse(
            cancelled=cancelled_jobs, completed=completed_jobs, ongoing=ongoing_jobs
        )

    except Exception as e:
        logger.error(f"Error fetching seeker job history: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the job history"
        )
