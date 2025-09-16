# app/api/v1/endpoints/verify_otp.py
import logging
import math
import random
from datetime import datetime
from typing import Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.websocket_manager import manager

router = APIRouter()

logger = logging.getLogger(__name__)


class VerifyOTPRequest(BaseModel):
    job_id: str
    otp: int


def generate_otp():
    return random.randint(1000, 9999)  # Generates a 4-digit OTP


async def verify_start_otp(job_id: str, otp: int, user_id: str, session):
    job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)}, session=session)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if str(job["assigned_to"]) != user_id:
        raise HTTPException(
            status_code=403, detail="You are not authorized to verify this OTP"
        )

    job_otp = job.get("job_start_otp", {})
    if job_otp.get("is_verified", False):
        raise HTTPException(status_code=400, detail="OTP has already been verified")

    if job_otp.get("OTP") != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    job_done_otp = generate_otp()
    current_time = datetime.utcnow()

    # Update the job document
    update_result = await motor_db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "job_start_otp.is_verified": True,
                "job_start_otp.verified_at": current_time,
                "job_done_otp": {"OTP": job_done_otp, "is_verified": False},
            }
        },
        session=session,
    )

    if update_result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to update the job record")

    # Mark the active_job_locations document as inactive
    active_job_update = await motor_db.active_job_locations.update_one(
        {"job_id": ObjectId(job_id)},
        {"$set": {"status": "inactive", "last_updated": current_time}},
        session=session,
    )

    if active_job_update.modified_count != 1:
        logger.warning(f"No active job location found for job {job_id}")

        # Send simplified WebSocket notification to the provider
    await manager.send_personal_message(
        {
            "type": "job_start_otp",
            "message": "Job start OTP verified",
            "job_id": job_id,
        },
        str(job["user_id"]),
    )

    return current_time


async def verify_done_otp(job_id: str, otp: int, user_id: str, session):
    job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)}, session=session)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if str(job["assigned_to"]) != user_id:
        raise HTTPException(
            status_code=403, detail="You are not authorized to verify this OTP"
        )

    if not job.get("job_start_otp", {}).get("is_verified", False):
        raise HTTPException(
            status_code=400, detail="Job start OTP has not been verified yet"
        )

    job_done_otp = job.get("job_done_otp", {})
    if job_done_otp.get("is_verified", False):
        raise HTTPException(
            status_code=400, detail="Job done OTP has already been verified"
        )

    if job_done_otp.get("OTP") != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    start_time = job["job_start_otp"]["verified_at"]
    end_time = datetime.utcnow()
    total_time = end_time - start_time
    total_minutes = total_time.total_seconds() / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)

    total_hours_worked = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
    total_hours_worked_numeric = round(total_minutes / 60, 2)
    billable_hours = math.ceil(total_minutes / 60)
    total_amount = billable_hours * job["current_rate"]

    job_update_result = await motor_db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "job_done_otp.is_verified": True,
                "job_done_otp.verified_at": end_time,
                "status": "completed",
                "total_hours_worked": total_hours_worked,
                "total_hours_worked_numeric": total_hours_worked_numeric,
                "billable_hours": billable_hours,
                "total_amount": total_amount,
            }
        },
        session=session,
    )

    if job_update_result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to update the job record")

    user_stats_update_result = await motor_db.user_stats.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$set": {
                "seeker_stats.user_status.current_status": "free",
                "seeker_stats.user_status.current_job_id": None,
                "seeker_stats.user_status.reason": "Job completed",
                "seeker_stats.user_status.status_updated_at": end_time,
            },
            "$inc": {
                "seeker_stats.total_jobs_done": 1,
                "seeker_stats.total_hours_worked": billable_hours,
                "seeker_stats.total_earned": total_amount,
            },
        },
        session=session,
    )

    if user_stats_update_result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to update user status")

        # Send simplified WebSocket notification to the provider
    await manager.send_personal_message(
        {"type": "job_done_otp", "message": "Job done OTP verified", "job_id": job_id},
        str(job["user_id"]),
    )

    return {
        "verified_at": end_time,
        "total_hours_worked": total_hours_worked,
        "total_hours_worked_numeric": total_hours_worked_numeric,
        "billable_hours": billable_hours,
        "total_amount": total_amount,
    }


@router.post(
    "/start-otp", response_model=Dict, dependencies=[Depends(role_required("seeker"))]
)
async def verify_job_start_otp(
    otp_request: VerifyOTPRequest, current_user: dict = Depends(get_current_user)
):
    async with await motor_db.client.start_session() as session:
        async with session.start_transaction():
            try:
                verified_at = await verify_start_otp(
                    otp_request.job_id,
                    otp_request.otp,
                    current_user["user_id"],
                    session,
                )
                return {
                    "message": "Job start OTP verified, and job done OTP set successfully",
                    "verified_at": verified_at,
                }
            except HTTPException as he:
                await session.abort_transaction()
                raise he
            except Exception as e:
                await session.abort_transaction()
                raise HTTPException(
                    status_code=500, detail=f"An error occurred: {str(e)}"
                )


@router.post(
    "/done-otp", response_model=Dict, dependencies=[Depends(role_required("seeker"))]
)
async def verify_job_done_otp(
    otp_request: VerifyOTPRequest, current_user: dict = Depends(get_current_user)
):
    async with await motor_db.client.start_session() as session:
        async with session.start_transaction():
            try:
                result = await verify_done_otp(
                    otp_request.job_id,
                    otp_request.otp,
                    current_user["user_id"],
                    session,
                )
                return {
                    "message": "Job done OTP verified successfully, job marked as completed, and user status updated",
                    **result,
                }
            except HTTPException as he:
                await session.abort_transaction()
                raise he
            except Exception as e:
                await session.abort_transaction()
                raise HTTPException(
                    status_code=500, detail=f"An error occurred: {str(e)}"
                )
