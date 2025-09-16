# app/api/v1/endpoints/admin/job_manager.py

import logging
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants for module and actions
MODULE = "jobs"
ACTIONS = {"VIEW": "read", "UPDATE": "update"}


@router.get("/jobs")
async def get_all_jobs(
        search: Optional[str] = Query(None, description="Search by Task ID or title"),
        status: Optional[str] = Query(None, description="Filter by status"),
        category_id: Optional[str] = Query(None, description="Filter by category"),
        city_id: Optional[str] = Query(None, description="Filter by city"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, gt=0, le=100, description="Items per page"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        # Calculate skip
        skip = (page - 1) * limit

        # Build query
        query = {}

        if search:
            # Search by job ID or title
            query["$or"] = [
                {"task_id": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
            ]

        if status and status != "all":
            query["status"] = status

        if category_id and category_id != "all":
            query["category_id"] = ObjectId(category_id)

        if city_id and city_id != "all":
            query["address_snapshot.city_id"] = ObjectId(city_id)

        # Get total count
        total_count = await motor_db.jobs.count_documents(query)

        # Fetch jobs with pagination
        cursor = (
            motor_db.jobs.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )

        jobs = []
        async for job in cursor:
            # Get category details
            category = await motor_db.categories.find_one(
                {"_id": job.get("category_id")}
            )
            category_name = category.get("name") if category else "Unknown"

            # Get city details
            city_id = job.get("address_snapshot", {}).get("city_id")
            city = await motor_db.cities.find_one({"_id": city_id}) if city_id else None
            city_name = (
                city.get("name")
                if city
                else job.get("address_snapshot", {}).get("address_line1", "")
            )

            # Prepare job data
            job_data = {
                "id": str(job["_id"]),
                "task_id": str(job["task_id"]),
                "title": job.get("title", ""),
                "category": category_name,
                "category_id": str(job.get("category_id", "")),
                "city": city_name,
                "city_id": str(city_id) if city_id else None,
                "status": job.get("status", ""),
                "created_at": (
                    job.get("created_at").isoformat() if job.get("created_at") else ""
                ),
            }

            jobs.append(job_data)

        # Get all cities for filtering
        cities_cursor = motor_db.cities.find({"is_served": True})
        cities = []
        async for city in cities_cursor:
            cities.append({"id": str(city["_id"]), "name": city["name"]})

        # Get all categories for filtering
        categories_cursor = motor_db.categories.find({})
        categories = []
        async for category in categories_cursor:
            categories.append({"id": str(category["_id"]), "name": category["name"]})

        return {
            "data": jobs,
            "filters": {"cities": cities, "categories": categories},
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": limit,
                "total_pages": (total_count + limit - 1) // limit,
            },
        }

    except PyMongoError as e:
        logger.error(f"Database error in get_all_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/jobs/{job_id}")
async def get_job_details(
    job_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        # Convert string ID to ObjectId and find job
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get category details
        category = await motor_db.categories.find_one({"_id": job.get("category_id")})
        category_name = category.get("name") if category else "Unknown"

        # Get city details
        city_id = job.get("address_snapshot", {}).get("city_id")
        city = await motor_db.cities.find_one({"_id": city_id}) if city_id else None
        city_name = (
            city.get("name")
            if city
            else job.get("address_snapshot", {}).get("address_line1", "")
        )

        # Convert ObjectId to string in address_snapshot
        address_snapshot = job.get("address_snapshot", {}).copy()
        if "_id" in address_snapshot:
            address_snapshot["_id"] = str(address_snapshot["_id"])
        if "city_id" in address_snapshot:
            address_snapshot["city_id"] = str(address_snapshot["city_id"])

        # Get provider details (user_id in job)
        provider_details = None
        if job.get("user_id"):
            provider = await motor_db.users.find_one({"_id": job["user_id"]})
            if provider:
                provider_stats = await motor_db.user_stats.find_one(
                    {"user_id": job["user_id"]}
                )
                if provider_stats:
                    provider_details = {
                        "profile": {
                            "name": provider_stats.get("personal_info", {}).get(
                                "name", ""
                            ),
                            "gender": provider_stats.get("personal_info", {}).get(
                                "gender"
                            ),
                            "profile_image": provider_stats.get(
                                "personal_info", {}
                            ).get("profile_image", ""),
                        },
                        "stats": {
                            "total_jobs_completed": provider_stats.get(
                                "provider_stats", {}
                            ).get("total_jobs_completed", 0),
                            "avg_rating": provider_stats.get("provider_stats", {}).get(
                                "avg_rating", 0
                            ),
                            "total_reviews": provider_stats.get(
                                "provider_stats", {}
                            ).get("total_reviews", 0),
                        },
                        "mobile": provider.get("mobile", ""),
                    }

        # Get seeker details (assigned_to in job)
        seeker_details = None
        if job.get("assigned_to"):
            seeker = await motor_db.users.find_one({"_id": job["assigned_to"]})
            if seeker:
                seeker_stats = await motor_db.user_stats.find_one(
                    {"user_id": job["assigned_to"]}
                )
                if seeker_stats:
                    seeker_details = {
                        "profile": {
                            "name": seeker_stats.get("personal_info", {}).get(
                                "name", ""
                            ),
                            "gender": seeker_stats.get("personal_info", {}).get(
                                "gender"
                            ),
                            "profile_image": seeker_stats.get("personal_info", {}).get(
                                "profile_image", ""
                            ),
                        },
                        "stats": {
                            "total_jobs_done": seeker_stats.get("seeker_stats", {}).get(
                                "total_jobs_done", 0
                            ),
                            "avg_rating": seeker_stats.get("seeker_stats", {}).get(
                                "avg_rating", 0
                            ),
                            "total_reviews": seeker_stats.get("seeker_stats", {}).get(
                                "total_reviews", 0
                            ),
                        },
                        "mobile": seeker.get("mobile", ""),
                    }

        # Convert OTP ObjectIds if present
        job_start_otp = (
            job.get("job_start_otp", {}).copy() if job.get("job_start_otp") else None
        )
        if job_start_otp and job_start_otp.get("verified_at"):
            job_start_otp["verified_at"] = job_start_otp["verified_at"].isoformat()

        job_done_otp = (
            job.get("job_done_otp", {}).copy() if job.get("job_done_otp") else None
        )
        if job_done_otp and job_done_otp.get("verified_at"):
            job_done_otp["verified_at"] = job_done_otp["verified_at"].isoformat()

        # Prepare payment status with proper date handling
        payment_status = job.get("payment_status", {}).copy()
        if payment_status and payment_status.get("paid_at"):
            payment_status["paid_at"] = payment_status["paid_at"].isoformat()

        # Get review details
        provider_review = job.get("provider_review", {}).copy()
        if provider_review:
            provider_review["provider_review_id"] = str(
                provider_review.get("provider_review_id")
            )
            if provider_review.get("reviewed_at"):
                provider_review["reviewed_at"] = provider_review[
                    "reviewed_at"
                ].isoformat()

        seeker_review = job.get("seeker_review", {}).copy()
        if seeker_review:
            seeker_review["seeker_review_id"] = str(
                seeker_review.get("seeker_review_id")
            )
            if seeker_review.get("reviewed_at"):
                seeker_review["reviewed_at"] = seeker_review["reviewed_at"].isoformat()

        # Prepare job data with all ObjectId fields converted to strings
        job_data = {
            "id": str(job["_id"]),
            "task_id": str(job["task_id"]),
            "title": job.get("title", ""),
            "description": job.get("description", ""),
            "category": category_name,
            "category_id": str(job.get("category_id", "")),
            "city": city_name,
            "city_id": str(city_id) if city_id else None,
            "status": job.get("status", ""),
            "created_at": (
                job.get("created_at").isoformat() if job.get("created_at") else ""
            ),
            "hourly_rate": job.get("hourly_rate", 0),
            "total_amount": job.get("total_amount", 0),
            "estimated_time": job.get("estimated_time", 0),
            "total_hours_worked": job.get("total_hours_worked", ""),
            "billable_hours": job.get("billable_hours", 0),
            "payment_status": payment_status,
            "address_snapshot": address_snapshot,
            "job_start_otp": job_start_otp,
            "job_done_otp": job_done_otp,
            "is_reached": job.get("is_reached", False),
            "reached_at": (
                job.get("reached_at").isoformat() if job.get("reached_at") else None
            ),
            "job_booking_time": (
                job.get("job_booking_time").isoformat()
                if job.get("job_booking_time")
                else None
            ),
            "provider_details": provider_details,
            "seeker_details": seeker_details,
            "provider_review": provider_review,
            "seeker_review": seeker_review,
            "user_id": str(job.get("user_id")) if job.get("user_id") else None,
            "assigned_to": (
                str(job.get("assigned_to")) if job.get("assigned_to") else None
            ),
        }

        return {"data": job_data}

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    except PyMongoError as e:
        logger.error(f"Database error in get_job_details: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_job_details: {str(e)}")
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
