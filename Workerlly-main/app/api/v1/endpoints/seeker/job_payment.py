from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required

router = APIRouter()


class PaymentRequest(BaseModel):
    job_id: str
    payment_method: str


@router.post(
    "/job-payment", response_model=dict, dependencies=[Depends(role_required("seeker"))]
)
async def process_job_payment(
    payment_request: PaymentRequest, current_user: dict = Depends(get_current_user)
):
    # Validate payment method
    if payment_request.payment_method not in ["cash", "online"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment method. Must be 'cash' or 'online'.",
        )

    # Retrieve the job from the database
    job = await motor_db.jobs.find_one({"_id": ObjectId(payment_request.job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if the current user is the assigned seeker
    if str(job["assigned_to"]) != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to process payment for this job",
        )

    # Check if the job is completed
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, detail="Payment can only be processed for completed jobs"
        )

    # Check if payment has already been processed
    if job.get("payment_status", {}).get("paid", False):
        raise HTTPException(
            status_code=400, detail="Payment has already been processed for this job"
        )

    # Prepare the update data
    update_data = {
        "payment_status": {
            "paid": True,
            "payment_method": payment_request.payment_method,
            "paid_at": datetime.utcnow(),
        },
        "provider_review": {
            "provider_review_done": False,
            "provider_review_id": None,
            "reviewed_at": None,
        },
        "seeker_review": {
            "seeker_review_done": False,
            "seeker_review_id": None,
            "reviewed_at": None,
        },
    }

    # Update the job with payment information and review placeholders
    update_result = await motor_db.jobs.update_one(
        {"_id": ObjectId(payment_request.job_id)}, {"$set": update_data}
    )

    if update_result.modified_count == 1:
        return {
            "message": "Payment processed successfully",
            "job_id": payment_request.job_id,
            "payment_method": payment_request.payment_method,
            "amount_paid": job["total_amount"],
        }
    else:
        raise HTTPException(
            status_code=500, detail="Failed to update the job payment status"
        )
