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


async def update_wallet_and_create_transaction(
    user_id: ObjectId,
    amount: float,
    description: str,
    job_id: ObjectId,
    session,
):
    logger.info(
        f"Updating wallet and creating transaction for user: {user_id}, amount: {amount}, description: {description}, job_id: {job_id}"
    )

    # Update the seeker's wallet balance
    await motor_db.user_stats.update_one(
        {"user_id": user_id},
        {"$inc": {"seeker_stats.wallet_balance": amount}},
        session=session,
    )
    logger.info(f"Updated wallet balance for user: {user_id}")

    # Create a new transaction record
    transaction = {
        "user_id": user_id,
        "amount": amount,
        "transaction_type": "credit" if amount > 0 else "debit",
        "description": description,
        "job_id": job_id,
        "created_at": datetime.utcnow(),
    }
    await motor_db.transactions.insert_one(transaction, session=session)
    logger.info(f"Created new transaction record: {transaction}")


@router.post(
    "/cancel-job/{job_id}",
    # response_model=BidResponse,
    dependencies=[Depends(role_required("seeker"))],
)
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    logger.info(f"Cancelling job: {job_id} for user: {current_user['user_id']}")
    user_id = ObjectId(current_user["user_id"])

    # Find the ongoing bid for the job
    bid = await motor_db.bids.find_one(
        {
            "job_id": ObjectId(job_id),
            "user_id": user_id,
            "status": "accepted",
        }
    )
    if not bid:
        logger.error(f"No ongoing job found for user: {user_id}")
        raise HTTPException(status_code=404, detail="No ongoing job found.")

    # Check if the job is within the 5-minute window of being "ongoing"
    ongoing_time = datetime.utcnow() - bid["updated_at"]
    if ongoing_time.total_seconds() > 300:
        logger.error(
            f"Job cannot be cancelled after 5 minutes. Ongoing time: {ongoing_time.total_seconds()} seconds"
        )
        raise HTTPException(
            status_code=400, detail="Job cannot be cancelled after 5 minutes."
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
                    {"$set": {"status": "cancelled", "reason": "Cancelled by Seeker"}},
                    session=session,
                )
                logger.info(f"Updated job status to 'cancelled' for job: {job_id}")

                # Retrieve the original transaction for the job
                transaction = await motor_db.transactions.find_one(
                    {
                        "user_id": user_id,
                        "job_id": ObjectId(job_id),
                        "transaction_type": "debit",
                    }
                )
                if not transaction:
                    logger.error(f"No transaction found for refund for user: {user_id}")
                    raise HTTPException(
                        status_code=404, detail="No transaction found for this job."
                    )

                # Refund Exact amount
                refund_amount = transaction["amount"]  # Should be a negative value

                # Refund the exact amount to the seeker's wallet
                await update_wallet_and_create_transaction(
                    user_id,
                    -refund_amount,
                    "Refund for cancelled job",
                    ObjectId(job_id),
                    session,
                )
                logger.info(
                    f"Refunded 100 Rs to user: {user_id} for cancelled job: {job_id}"
                )

                # Update the seeker's user_status to "free" with the reason "Job cancelled by seeker"
                await motor_db.user_stats.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "seeker_stats.user_status": {
                                "current_status": "free",
                                "current_job_id": None,
                                "reason": "Job cancelled by seeker",
                                "status_updated_at": datetime.utcnow(),
                            }
                        }
                    },
                    session=session,
                )
                logger.info(
                    f"Updated seeker's user_status to 'free' for user: {user_id}"
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

                # Send a WebSocket notification to the provider about the job cancellation
                result = await motor_db.jobs.find_one(
                    {"_id": ObjectId(job_id)}, {"user_id": 1, "_id": 0}
                )

                provider_id = str(result["user_id"]) if result else None

                await manager.broadcast(
                    {
                        "type": "job_cancel_by_seeker",
                        "data": {
                            "job_id": job_id,
                        },
                    },
                    user_id=str(provider_id),
                )
                logger.info(
                    f"Sent WebSocket notification about job cancellation to provider: {provider_id}"
                )

                # Return the updated bid
                updated_bid = await motor_db.bids.find_one(
                    {"_id": bid["_id"]}, session=session
                )
                return {"message": "Job has been cancelled"}

            except Exception as e:
                logger.error(f"Error cancelling the job: {e}")
                raise HTTPException(status_code=500, detail="Error cancelling the job.")
