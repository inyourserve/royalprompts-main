# File: app/api/v1/endpoints/provider_job_history.py

import logging
from datetime import datetime
from typing import List

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
    sub_category_name: str
    created_at: datetime


class JobHistoryResponse(BaseModel):
    pending: List[JobHistoryItem]
    ongoing: List[JobHistoryItem]
    completed: List[JobHistoryItem]
    cancelled: List[JobHistoryItem]


@router.get(
    "/jobs-history",
    response_model=JobHistoryResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def get_provider_job_history(current_user: dict = Depends(get_current_user)):
    try:
        user_id = ObjectId(current_user["user_id"])

        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category",
                }
            },
            {"$unwind": "$category"},
            {
                "$addFields": {
                    "sub_category": {
                        "$filter": {
                            "input": "$category.sub_categories",
                            "as": "sub",
                            "cond": {"$in": ["$$sub.id", "$sub_category_ids"]},
                        }
                    }
                }
            },
            {"$unwind": "$sub_category"},
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "status": 1,
                    "created_at": 1,
                    "sub_category_name": "$sub_category.name",
                }
            },
        ]

        jobs = await motor_db.jobs.aggregate(pipeline).to_list(None)

        def create_job_item(job):
            return JobHistoryItem(
                id=str(job["_id"]),
                title=job.get("title", "Untitled Job"),
                status=job.get("status", "pending"),
                sub_category_name=job.get("sub_category_name", "Unknown"),
                created_at=job.get("created_at", datetime.utcnow()),
            )

        pending_jobs = [
            create_job_item(job) for job in jobs if job.get("status") == "pending"
        ]
        ongoing_jobs = [
            create_job_item(job) for job in jobs if job.get("status") == "ongoing"
        ]
        completed_jobs = [
            create_job_item(job) for job in jobs if job.get("status") == "completed"
        ]
        cancelled_jobs = [
            create_job_item(job) for job in jobs if job.get("status") == "cancelled"
        ]

        return JobHistoryResponse(
            pending=pending_jobs,
            ongoing=ongoing_jobs,
            completed=completed_jobs,
            cancelled=cancelled_jobs,
        )

    except Exception as e:
        logger.error(f"Error fetching provider job history: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the job history"
        )
