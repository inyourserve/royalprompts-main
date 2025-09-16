import logging
from datetime import timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.provider_job_response import ProviderJobResponse
from app.db.helpers.reviews_helper import fetch_reviews_for_job
from app.db.helpers.user_helpers import fetch_user_mobile
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/provider-jobs/{job_id}",
    response_model=ProviderJobResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def get_provider_job_details(
    job_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if str(job["user_id"]) != str(current_user["user_id"]):
            raise HTTPException(
                status_code=403, detail="You do not have access to this job"
            )

        category = await motor_db.categories.find_one(
            {"_id": ObjectId(job["category_id"])}
        )
        seeker_stats_doc = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(job.get("assigned_to"))}
        )

        seeker_stats = extract_user_stats(seeker_stats_doc) if seeker_stats_doc else {}
        seeker_info = seeker_stats.get("seeker_stats", {})
        personal_info = seeker_stats.get("personal_info", {})

        job_booking_time = job.get("job_booking_time", None)

        job_start_otp = job.get("job_start_otp", {})
        job_done_otp = job.get("job_done_otp", {})

        estimated_time = job.get("estimated_time", 0)
        reaching_time = None
        if job_booking_time:
            reaching_time = job_booking_time + timedelta(minutes=estimated_time)
        reviews = await fetch_reviews_for_job(job)

        # # Fetch provider review details
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
        # Fetch seeker's mobile number
        seeker_mobile = (
            await fetch_user_mobile(
                user_id=str(job.get("assigned_to", "")), role="seeker"
            )
            if job.get("assigned_to")
            else None
        )
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
        job_response = {
            "_id": str(job["_id"]),
            "seeker": {
                "id": str(job.get("assigned_to", "")),
                "name": personal_info.get("name", "Unknown Seeker"),
                "mobile": seeker_mobile,
                "profile_image": personal_info.get("profile_image", ""),
                "category": seeker_info.get("category", {}).get(
                    "category_name", "Unknown Category"
                ),
                "avg_rating": seeker_info.get("avg_rating", 0),
            },
            "job_summary": {
                "title": job.get("title", ""),
                "description": job.get("description", ""),
                "current_rate": job.get("current_rate", 0),
                "booking_time": job_booking_time,
            },
            "job_meta": {
                "status": job.get("status", "Unknown"),
                "is_reached": job.get("is_reached"),
                "work_category": (
                    category.get("name", "Unknown Category")
                    if category
                    else "Unknown Category"
                ),
                "estimated_time": estimated_time,
                "reaching_time": reaching_time,
                "job_booking_time": job.get("job_booking_time"),
                "job_start_otp": job_start_otp.get("OTP"),
                "job_start_otp_verified": job_start_otp.get("is_verified"),
                "job_started_at": job_start_otp.get("verified_at"),
                "job_done_otp": job_done_otp.get("OTP"),
                "job_done_otp_verified": job_done_otp.get("is_verified"),
                "job_done_at": job_done_otp.get("verified_at"),
                "total_hours_worked": job.get("total_hours_worked"),
                "total_amount": job.get("total_amount"),
                "paid": job.get("payment_status", {}).get("paid", False),
                "reason": job.get("reason", None),
            },
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
            # # },
            # "seeker_review": {
            #     "seeker_review_done": seeker_review.get("seeker_review_done", False),
            #     "seeker_review_id": str(seeker_review_id) if seeker_review_id else None,
            #     "rating": review_details.get("rating"),
            #     "review": review_details.get("review"),
            #     "reviewed_at": seeker_review.get("reviewed_at"),
            # },
            **reviews,  # Inject seeker_review and provider_review directly
        }

        return ProviderJobResponse(**job_response)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching provider job details for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the job details"
        )
