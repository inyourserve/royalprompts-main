import logging
from datetime import datetime
from typing import Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies.auth import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required

router = APIRouter()
logger = logging.getLogger(__name__)


@router.patch(
    "/reached",
    response_model=Dict[str, str],
    dependencies=[Depends(role_required("seeker"))],
)
async def mark_job_reached(
    job_id: str = Query(..., description="ID of the job to mark as reached"),
    current_user: dict = Depends(get_current_user),
):
    user_id = ObjectId(current_user["user_id"])
    session = await motor_db.client.start_session()
    try:
        async with session.start_transaction():
            # Find the job and ensure it's assigned to the current user
            job = await motor_db.jobs.find_one(
                {"_id": ObjectId(job_id), "assigned_to": user_id},
                session=session,
            )
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or you don't have permission to update it",
                )

            # Check if the job is already marked as reached
            if job.get("is_reached", False):
                raise HTTPException(
                    status_code=400,
                    detail="You have already marked this job as reached",
                )

            # Check if the job status is ongoing
            if job["status"] != "ongoing":
                raise HTTPException(
                    status_code=400,
                    detail="Only ongoing jobs can be marked as reached",
                )

            # Update the job to mark it as reached
            update_result = await motor_db.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "is_reached": True,
                        "reached_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
                session=session,
            )
            if update_result.modified_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to update job as reached",
                )

            # Update seeker stats (if needed)
            # await motor_db.user_stats.update_one(
            #     {"user_id": user_id},
            #     {"$inc": {"seeker_stats.total_jobs_reached": 1}},
            #     session=session,
            # )

            return {"message": "Job has been marked as reached"}
    except Exception as e:
        logger.error(f"Failed to mark job as reached: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark job as reached")
    finally:
        await session.end_session()
