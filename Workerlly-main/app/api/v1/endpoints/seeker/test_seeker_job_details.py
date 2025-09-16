import logging
from datetime import timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.seeker_job_response import JobResponse
from app.db.helpers.reviews_helper import fetch_reviews_for_job
from app.db.helpers.user_helpers import fetch_user_mobile
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_category_details(category_id: ObjectId) -> dict:
    category = await motor_db.categories.find_one({"_id": category_id})
    if category:
        return {
            "name": category["name"],
            "thumbnail": category.get("thumbnail", "default_category_thumbnail.jpg"),
            "sub_categories": category.get("sub_categories", []),
        }
    return {
        "name": "Unknown Category",
        "thumbnail": "default_category_thumbnail.jpg",
        "sub_categories": [],
    }


async def get_subcategories_details(category: dict, sub_category_ids: list) -> list:
    sub_categories = category.get("sub_categories", [])
    subcategory_names = []
    subcategory_thumbnails = []

    for sub_cat in sub_categories:
        if any(str(sub_cat["id"]) == str(sub_id) for sub_id in sub_category_ids):
            subcategory_names.append(sub_cat["name"])
            subcategory_thumbnails.append(
                sub_cat.get("thumbnail", "default_subcategory_thumbnail.jpg")
            )

    return subcategory_names, subcategory_thumbnails


@router.get(
    "/seeker-jobs/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(role_required("seeker"))],
)
async def get_seeker_job_details(
    job_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if "assigned_to" not in job or str(job["assigned_to"]) != str(
            current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403, detail="You do not have access to this job"
            )

        category_id = ObjectId(job["category_id"])
        category_details = await get_category_details(category_id)
        subcategory_names, subcategory_thumbnails = await get_subcategories_details(
            category_details, job["sub_category_ids"]
        )

        provider_stats_doc = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(job["user_id"])}
        )
        provider_stats = (
            extract_user_stats(provider_stats_doc) if provider_stats_doc else {}
        )
        provider_info = provider_stats.get("provider_stats", {})
        personal_info = provider_stats.get("personal_info", {})

        address_snapshot = job.get("address_snapshot", {})
        location = address_snapshot.get("location", {})
        coordinates = location.get("coordinates", [0, 0])

        job_booking_time = job.get("job_booking_time")
        is_reached = job.get("is_reached")

        estimated_time = job.get("estimated_time", 0)
        reaching_time = None
        if job_booking_time:
            reaching_time = job_booking_time + timedelta(minutes=estimated_time)

        reviews = await fetch_reviews_for_job(job)

        # # Fetch seeker review details
        # seeker_review = job.get("seeker_review", {})
        # seeker_review_id = seeker_review.get("seeker_review_id")
        # review_details = {}
        # if seeker_review_id:
        #     review = await motor_db.reviews.find_one({"_id": seeker_review_id})
        #     if review:
        #         review_details = {
        #             "rating": review.get("rating"),
        #             "review": review.get("review"),
        #         }
        # Fetch provider's mobile number
        provider_mobile = await fetch_user_mobile(
            user_id=str(job.get("user_id", "")), role="provider"
        )
        # Fetch provider review details
        # provider_review = job.get("provider_review", {})
        # provider_review_id = provider_review.get("provider_review_id")
        # review_details = {}
        # if provider_review_id:
        #     review = await motor_db.reviews.find_one({"_id": provider_review_id})
        #     if review:
        #         review_details = {
        #             "rating": review.get("rating"),
        #             "review": review.get("review"),
        #         }
        job_response = {
            "_id": str(job["_id"]),
            "provider": {
                "id": str(job["user_id"]),
                "name": personal_info.get("name", "Unknown Provider"),
                "mobile": provider_mobile,
                "profile_image": personal_info.get("profile_image", ""),
                "avg_rating": provider_info.get("avg_rating", 0),
            },
            "job_summary": {
                "title": job.get("title", ""),
                "description": job.get("description", ""),
                "current_rate": job.get("current_rate", 0),
                "booking_time": job.get("job_booking_time", ""),
                "updated_at": job.get("updated_at", ""),
            },
            "address": {
                "_id": str(address_snapshot.get("_id", "")),
                "city_id": str(address_snapshot.get("city_id", "")),
                "address_line1": address_snapshot.get("address_line1", ""),
                "apartment_number": address_snapshot.get("apartment_number", ""),
                "landmark": address_snapshot.get("landmark", ""),
                "label": address_snapshot.get("label", ""),
                "latitude": coordinates[1] if len(coordinates) > 1 else 0,
                "longitude": coordinates[0] if len(coordinates) > 0 else 0,
                "location": location,
            },
            "job_meta": {
                "status": job.get("status", "Unknown"),
                "is_reached": is_reached,
                "estimated_time": estimated_time,
                "reaching_time": reaching_time,
                "job_started_at": job.get("job_start_otp", {}).get("verified_at"),
                "job_done_at": job.get("job_done_otp", {}).get("verified_at"),
                "total_hours_worked": job.get("total_hours_worked"),
                "total_amount": job.get("total_amount"),
                "paid": job.get("payment_status", {}).get("paid", False),
                "payment_method": job.get("payment_status", {}).get("payment_method"),
                "reason": job.get("reason", None),
            },
            "work_category": {
                "category_name": category_details["name"],
                "category_thumbnail": category_details["thumbnail"],
                "subcategory_name": subcategory_names,
                "subcategory_thumbnail": subcategory_thumbnails,
            },
            # "seeker_review": {
            #     "seeker_review_done": seeker_review.get("seeker_review_done", False),
            #     "seeker_review_id": str(seeker_review_id) if seeker_review_id else None,
            #     "rating": review_details.get("rating"),
            #     "review": review_details.get("review"),
            #     "reviewed_at": seeker_review.get("reviewed_at"),
            # },
            # "provider_review": {
            #     "provider_review_done": provider_review.get(
            #         "provider_review_done", False
            #     ),
            #     "provider_review_id": (
            #         str(provider_review_id) if provider_review_id else None
            #     ),
            #     "rating": review_details.get("rating"),
            #     "review": review_details.get("review"),
            #     "reviewed_at": provider_review.get("reviewed_at"),
            # },
            **reviews,
        }

        return JobResponse(**job_response)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching seeker job details for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the job details"
        )
