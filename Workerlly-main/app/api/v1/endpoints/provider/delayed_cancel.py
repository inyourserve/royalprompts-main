import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/delayed-cancel/{job_id}",
    dependencies=[Depends(role_required("provider"))],
)
async def provider_cancel_job_after_45(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    logger.info(
        f"Provider cancelling job after 45 minutes: {job_id} for provider: {current_user['user_id']}"
    )
    provider_id = ObjectId(current_user["user_id"])

    # Find the job and verify it belongs to the current provider
    job = await motor_db.jobs.find_one(
        {
            "_id": ObjectId(job_id),
            "user_id": provider_id,  # Provider is the job creator
            "status": "ongoing",  # Only ongoing jobs can be cancelled
        }
    )

    if not job:
        logger.error(f"No ongoing job found for provider: {provider_id}")
        raise HTTPException(
            status_code=404,
            detail="No ongoing job found or job doesn't belong to current provider.",
        )

    # Check if 45 minutes have passed since booking time
    booking_time = job.get("job_booking_time")
    if not booking_time:
        logger.error(f"Job booking time not found for job: {job_id}")
        raise HTTPException(status_code=400, detail="Invalid job booking time.")

    time_since_booking = datetime.utcnow() - booking_time
    if time_since_booking.total_seconds() < 2700:  # 45 minutes = 2700 seconds
        logger.error(
            f"Job cannot be cancelled before 45 minutes. Time since booking: {time_since_booking.total_seconds()} seconds"
        )
        raise HTTPException(
            status_code=400,
            detail="Job cannot be cancelled before 45 minutes from booking time.",
        )

    # Find the ongoing bid by the seeker
    bid = await motor_db.bids.find_one(
        {
            "job_id": ObjectId(job_id),
            "user_id": job["assigned_to"],  # Seeker's ID
            "status": "accepted",
        }
    )

    if not bid:
        logger.error(f"No accepted bid found for job: {job_id}")
        raise HTTPException(
            status_code=404, detail="No accepted bid found for this job."
        )

    async with await motor_db.client.start_session() as session:
        async with session.start_transaction():
            try:
                # Update the bid status to "cancelled"
                await motor_db.bids.update_one(
                    {"_id": bid["_id"]},
                    {"$set": {"status": "cancelled"}},
                    session=session,
                )
                logger.info(f"Updated bid status to 'cancelled' for bid: {bid['_id']}")

                # Update the job status to "cancelled" with the reason
                await motor_db.jobs.update_one(
                    {"_id": ObjectId(job_id)},
                    {
                        "$set": {
                            "status": "cancelled",
                            "reason": "Cancelled by Provider after 45 minutes",
                        }
                    },
                    session=session,
                )
                logger.info(f"Updated job status to 'cancelled' for job: {job_id}")

                # Update the provider's status to "free"
                await motor_db.user_stats.update_one(
                    {"user_id": provider_id},
                    {
                        "$set": {
                            "provider_stats.user_status": {
                                "current_status": "free",
                                "current_job_id": None,
                                "reason": "Job cancelled by provider after 45 minutes",
                                "status_updated_at": datetime.utcnow(),
                            }
                        }
                    },
                    session=session,
                )
                logger.info(
                    f"Updated provider's status to 'free' for provider: {provider_id}"
                )

                # Update the seeker's status to "free"
                await motor_db.user_stats.update_one(
                    {"user_id": job["assigned_to"]},
                    {
                        "$set": {
                            "seeker_stats.user_status": {
                                "current_status": "free",
                                "current_job_id": None,
                                "reason": "Job cancelled by provider after 45 minutes",
                                "status_updated_at": datetime.utcnow(),
                            }
                        }
                    },
                    session=session,
                )
                logger.info(
                    f"Updated seeker's status to 'free' for seeker: {job['assigned_to']}"
                )

                # Update the active job location status to "inactive"
                await motor_db.active_job_locations.update_one(
                    {"job_id": ObjectId(job_id)},
                    {"$set": {"status": "inactive"}},
                    session=session,
                )
                logger.info(
                    f"Updated active job location status to 'inactive' for job: {job_id}"
                )

                # Send WebSocket notification to the seeker about the job cancellation
                await manager.broadcast(
                    {
                        "type": "delayed_cancel",
                        "data": {
                            "job_id": job_id,
                        },
                    },
                    user_id=str(job["assigned_to"]),
                )
                logger.info(
                    f"Sent WebSocket notification about job cancellation to seeker: {job['assigned_to']}"
                )

                return {
                    "message": "Job has been cancelled successfully",
                }

            except Exception as e:
                logger.error(f"Error cancelling the job: {e}")
                raise HTTPException(status_code=500, detail="Error cancelling the job.")
