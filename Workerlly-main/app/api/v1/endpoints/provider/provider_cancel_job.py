import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.bids import update_wallet_and_create_transaction
from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/cancel-job/{job_id}",
    dependencies=[Depends(role_required("provider"))],
)
async def provider_cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    logger.info(
        f"Provider cancelling job: {job_id} for provider: {current_user['user_id']}"
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

    # Check if the job is within the 5-minute window of booking time
    booking_time = job.get("job_booking_time")
    if not booking_time:
        logger.error(f"Job booking time not found for job: {job_id}")
        raise HTTPException(status_code=400, detail="Invalid job booking time.")
    current_time = datetime.utcnow()
    print(booking_time)

    ongoing_time = current_time - booking_time
    if ongoing_time.total_seconds() > 300:  # 5 minutes = 300 seconds
        logger.error(
            f"Job cannot be cancelled after 5 minutes. Ongoing time: {ongoing_time.total_seconds()} seconds"
        )
        raise HTTPException(
            status_code=400, detail="Job cannot be cancelled after 5 minutes."
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
                            "reason": "Cancelled by Provider",
                        }
                    },
                    session=session,
                )
                logger.info(f"Updated job status to 'cancelled' for job: {job_id}")

                # seeker's ID (assigned_to)
                seeker_id = job["assigned_to"]
                # Retrieve the original transaction for the job
                transaction = await motor_db.transactions.find_one(
                    {
                        "user_id": seeker_id,
                        "job_id": ObjectId(job_id),
                        "transaction_type": "debit",
                    }
                )
                if not transaction:
                    logger.error(
                        f"No transaction found for refund for user: {seeker_id}"
                    )
                    raise HTTPException(
                        status_code=404, detail="No transaction found for this job."
                    )

                # Refund Exact amount
                refund_amount = transaction["amount"]  # Should be a negative value
                # Refund the amount to seeker's wallet
                await update_wallet_and_create_transaction(
                    seeker_id,
                    -refund_amount,
                    "Refund for job cancelled by provider",
                    ObjectId(job_id),
                    session,
                )
                logger.info(
                    f"Refunded {job['current_rate']} to seeker: {job['assigned_to']} for cancelled job: {job_id}"
                )

                # Update the provider's status to "free"
                await motor_db.user_stats.update_one(
                    {"user_id": provider_id},
                    {
                        "$set": {
                            "provider_stats.user_status": {
                                "current_status": "free",
                                "current_job_id": None,
                                "reason": "Job cancelled by provider",
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
                                "reason": "Job cancelled by provider",
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
                        "type": "job_cancel_by_provider",
                        "data": {
                            "job_id": job_id,
                        },
                    },
                    user_id=str(job["assigned_to"]),
                )
                logger.info(
                    f"Sent WebSocket notification about job cancellation to seeker: {job['assigned_to']}"
                )

                return {"message": "Job has been cancelled successfully"}

            except Exception as e:
                logger.error(f"Error cancelling the job: {e}")
                raise HTTPException(status_code=500, detail="Error cancelling the job.")
