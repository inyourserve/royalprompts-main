import logging
from datetime import datetime, timezone
from typing import Dict

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

# Set up logging
logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Store the job ID for reference
SCHEDULER_JOB_ID = "cancel_inactive_jobs"

# Constants for module and actions
MODULE = "scheduler"
ACTIONS = {"VIEW": "read", "EXECUTE": "execute"}


async def update_user_status(user_id: ObjectId, current_time: datetime) -> Dict:
    """
    Update user status to free when job is cancelled
    """
    try:
        update = {
            "$set": {
                "seeker_stats.user_status": {
                    "current_status": "free",
                    "current_job_id": None,
                    "reason": None,
                    "status_updated_at": current_time,
                }
            }
        }

        result = await motor_db.user_stats.update_one({"user_id": user_id}, update)

        logger.info(f"Updated user status for user {user_id} to free")
        return {
            "status": "success",
            "message": f"Updated user status for user {user_id}",
        }
    except PyMongoError as e:
        logger.error(
            f"Database error updating user status for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error updating user status for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


async def update_active_job_locations(job_id: ObjectId, current_time: datetime) -> Dict:
    """
    Update active job locations status to inactive when job is cancelled
    """
    try:
        update = {"$set": {"status": "inactive", "last_updated": current_time}}

        result = await motor_db.active_job_locations.update_one(
            {"job_id": job_id, "status": "active"}, update
        )

        logger.info(f"Updated active job location status for job {job_id} to inactive")
        return {
            "status": "success",
            "message": f"Updated job location for job {job_id}",
        }
    except PyMongoError as e:
        logger.error(f"Database error updating job location for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error updating job location for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


async def cancel_inactive_jobs() -> Dict:
    """
    Function to cancel pending and ongoing jobs at midnight
    """
    try:
        current_time = datetime.utcnow()

        # Find all pending and ongoing jobs
        jobs_to_cancel = await motor_db.jobs.find(
            {"status": {"$in": ["pending", "ongoing"]}}
        ).to_list(length=None)

        cancelled_count = 0
        for job in jobs_to_cancel:
            job_id = job["_id"]
            try:
                # Update job status
                await motor_db.jobs.update_one(
                    {"_id": job_id},
                    {
                        "$set": {
                            "status": "cancelled",
                            "cancellation_reason": "cancelled by system",
                            "cancelled_at": current_time,
                            "updated_at": current_time,
                        }
                    },
                )

                # For ongoing jobs, update user status and active job locations
                if job.get("status") == "ongoing" and job.get("assigned_to"):
                    # Update seeker's status
                    await update_user_status(job["assigned_to"], current_time)

                    # Update active job locations
                    await update_active_job_locations(job_id, current_time)

                cancelled_count += 1

                logger.info(
                    f"Cancelled job {job_id}: "
                    f"Title: {job.get('title')}, "
                    f"Previous Status: {job.get('status')}, "
                    f"Created At: {job.get('created_at')}"
                )

            except Exception as e:
                logger.error(f"Error cancelling job {job_id}: {str(e)}")
                continue

        logger.info(f"Auto-cancelled {cancelled_count} jobs at {current_time}")
        return {
            "status": "success",
            "message": f"Successfully cancelled {cancelled_count} jobs",
            "cancelled_count": cancelled_count,
        }

    except PyMongoError as e:
        logger.error(f"Database error in cancel_inactive_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error in cancel_inactive_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.on_event("startup")
async def setup_scheduler():
    """
    Set up the scheduler to run at midnight (00:00)
    """
    try:
        # Schedule the job to run at midnight
        trigger = CronTrigger(hour=0, minute=0)
        scheduler.add_job(
            cancel_inactive_jobs,
            trigger=trigger,
            id=SCHEDULER_JOB_ID,
            name="Cancel Inactive Jobs at Midnight",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Job cancellation scheduler started successfully")

    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail="Error setting up scheduler")


@router.get("/scheduler-status")
async def get_scheduler_status(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """
    Get the status of the scheduler and next run time
    """
    try:
        job = scheduler.get_job(SCHEDULER_JOB_ID)
        if not job:
            return {
                "status": "error",
                "message": "Scheduler job not found",
                "next_run": None,
                "countdown": None,
            }

        # Get next run time
        next_run = job.next_run_time

        if next_run:
            # Convert to IST for display
            ist = pytz.timezone("Asia/Kolkata")
            next_run_ist = next_run.astimezone(ist)

            # Calculate countdown
            now = datetime.now(timezone.utc)
            time_diff = next_run - now

            # Convert to hours, minutes, seconds
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            seconds = int(time_diff.total_seconds() % 60)

            return {
                "status": "active",
                "next_run_utc": next_run.isoformat(),
                "next_run_ist": next_run_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
                "countdown": {
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds,
                    "total_seconds": int(time_diff.total_seconds()),
                },
            }
        else:
            return {
                "status": "inactive",
                "message": "No next run time scheduled",
                "next_run": None,
                "countdown": None,
            }

    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting scheduler status")


@router.post("/trigger-job-cancellation")
async def trigger_job_cancellation(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["EXECUTE"])),
):
    """
    Endpoint to manually trigger job cancellation (for testing purposes)
    """
    try:
        result = await cancel_inactive_jobs()
        return result
    except Exception as e:
        logger.error(f"Error triggering job cancellation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error triggering job cancellation")
