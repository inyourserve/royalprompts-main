import asyncio
import datetime
import logging

# Import your existing database connection and task ID generator
from app.db.models.database import motor_db
from app.utils.task_id_generator import TaskIDGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_task_ids_to_ist():
    """Update all existing task_ids to use IST timezone instead of UTC"""

    # Get all jobs that have a task_id
    jobs = await motor_db.jobs.find({"task_id": {"$exists": True}}).to_list(length=None)

    if not jobs:
        logger.info("No jobs found with task_ids to update")
        return

    logger.info(f"Found {len(jobs)} jobs with task_ids to update")

    # Group jobs by created_at date
    job_groups = {}
    for job in jobs:
        # Get created_at in UTC
        created_at_utc = job.get("created_at")

        # Convert to IST
        ist_offset = datetime.timedelta(hours=5, minutes=30)
        created_at_ist = created_at_utc + ist_offset

        # Create a date key for grouping
        date_key = created_at_ist.strftime("%Y-%m-%d")

        if date_key not in job_groups:
            job_groups[date_key] = []

        job_groups[date_key].append({
            "id": job["_id"],
            "created_at": created_at_utc,
            "created_at_ist": created_at_ist,
            "current_task_id": job["task_id"]
        })

    total_updated = 0
    for date_key, jobs in job_groups.items():
        # Get a sample date from this group
        sample_date = jobs[0]["created_at_ist"]
        year = sample_date.year
        month = sample_date.month
        day = sample_date.day

        # Get date-specific prefix based on IST date
        year_char = TaskIDGenerator._encode_year(year)
        month_char = TaskIDGenerator._encode_month(month)
        day_char = TaskIDGenerator._encode_day(day)
        date_prefix = f"{year_char}{month_char}{day_char}"

        # Sort jobs within day by created_at time
        jobs.sort(key=lambda x: x["created_at"])

        logger.info(
            f"Processing {len(jobs)} jobs for IST date {date_key} (UTC date prefix was {jobs[0]['current_task_id'][:3]}, new prefix {date_prefix})")

        # Assign sequential task_ids
        for i, job in enumerate(jobs, start=1):
            new_task_id = f"{date_prefix}-{i:04d}"
            old_task_id = job["current_task_id"]

            if new_task_id != old_task_id:
                logger.debug(f"Updating job {job['id']}: {old_task_id} -> {new_task_id}")

                try:
                    # Update the task_id
                    result = await motor_db.jobs.update_one(
                        {"_id": job["id"]},
                        {"$set": {"task_id": new_task_id}}
                    )

                    if result.modified_count > 0:
                        total_updated += 1
                        if i % 20 == 0:  # Log progress every 20 jobs
                            logger.info(f"Updated {i} of {len(jobs)} jobs for date {date_key}")
                except Exception as e:
                    logger.error(f"Error updating job {job['id']}: {str(e)}")

    logger.info(f"Migration completed. Updated {total_updated} jobs to use IST timezone.")


if __name__ == "__main__":
    logger.info("Starting migration to update task_ids from UTC to IST timezone")
    asyncio.run(migrate_task_ids_to_ist())
