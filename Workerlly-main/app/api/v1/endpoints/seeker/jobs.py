# File: app/api/v1/endpoints/seeker/jobs.py

import logging
from datetime import datetime
from typing import Dict, Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.jobseeker import (
    JobSeekerListResponse,
    JobListParams,
    UserProfile,
    JobSeekerView,
)
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/jobs",
    response_model=JobSeekerListResponse,
    dependencies=[Depends(role_required("seeker"))],
)
async def list_jobs_for_seeker(
    params: JobListParams = Depends(), current_user: dict = Depends(get_current_user)
):
    user_stats_doc = await motor_db.user_stats.find_one(
        {"user_id": ObjectId(current_user["user_id"])}
    )
    if not user_stats_doc:
        raise HTTPException(status_code=404, detail="User profile not found")

    user_stats = extract_user_stats(user_stats_doc)
    seeker_stats = user_stats.get("seeker_stats", {})

    user = UserProfile(
        id=str(user_stats_doc["user_id"]),
        category_id=str(seeker_stats.get("category", {}).get("category_id")),
        city_id=str(seeker_stats.get("city_id")),
    )

    query = {
        "status": "pending",
        "category_id": ObjectId(user.category_id),
        "address_snapshot.city_id": ObjectId(user.city_id),
    }

    if params.min_hourly_rate is not None or params.max_hourly_rate is not None:
        query["hourly_rate"] = {}
        if params.min_hourly_rate is not None:
            query["hourly_rate"]["$gte"] = params.min_hourly_rate
        if params.max_hourly_rate is not None:
            query["hourly_rate"]["$lte"] = params.max_hourly_rate

    total = await motor_db.jobs.count_documents(query)

    sort_field = params.sort_by
    sort_order = 1 if params.sort_order == "asc" else -1

    jobs = (
        await motor_db.jobs.find(query)
        .sort(sort_field, sort_order)
        .skip((params.page - 1) * params.page_size)
        .limit(params.page_size)
        .to_list(None)
    )

    provider_ids = [job.get("user_id") for job in jobs if job.get("user_id")]
    providers_docs = await motor_db.user_stats.find(
        {"user_id": {"$in": provider_ids}}
    ).to_list(None)
    provider_map = {}
    for provider_doc in providers_docs:
        provider_stats = extract_user_stats(provider_doc)
        provider_map[str(provider_doc["user_id"])] = provider_stats[
            "personal_info"
        ].get("name", "Unknown Provider")

    job_views = [
        JobSeekerView(
            id=str(job["_id"]),
            title=job.get("title", "Untitled Job"),
            description=job.get("description", "No description provided"),
            hourly_rate=job.get("hourly_rate", 0),
            city=job.get("address_snapshot", {}).get("label", "Unknown City"),
            provider_name=provider_map.get(str(job.get("user_id")), "Unknown Provider"),
            created_at=job.get("created_at", datetime.utcnow()),
        )
        for job in jobs
    ]

    return JobSeekerListResponse(
        jobs=job_views, total=total, page=params.page, page_size=params.page_size
    )


async def get_job_details(job_id: str) -> Dict[str, Any]:
    try:
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            return None

        provider_info = await get_provider_info(job["user_id"])

        return {
            "id": str(job["_id"]),
            "sub_category": await get_sub_category_name(job["sub_category_ids"][0]),
            "description": job.get("description", "No description provided"),
            "hourly_rate": job.get("hourly_rate", 0),
            "location": f"{job['address_snapshot']['label']}, {await get_city_name(job['address_snapshot']['city_id'])}",
            "provider_name": provider_info["name"],
            "provider_rating": provider_info["rating"],
            "distance": 0,  # Placeholder - implement actual distance calculation
        }
    except Exception as e:
        logger.error(f"Error fetching job details for {job_id}: {str(e)}")
        return None


async def get_provider_info(user_id: ObjectId) -> Dict[str, Any]:
    provider_doc = await motor_db.user_stats.find_one({"user_id": user_id})
    if provider_doc:
        provider_stats = extract_user_stats(provider_doc)
        provider_info = provider_stats.get("provider_stats", {})
        personal_info = provider_stats.get("personal_info", {})
        return {
            "name": personal_info.get("name", "Unknown Provider"),
            "rating": provider_info.get("avg_rating", 0),
        }
    return {"name": "Unknown Provider", "rating": 0}


async def get_sub_category_name(sub_category_id: ObjectId) -> str:
    category = await motor_db.categories.find_one(
        {"sub_categories.id": sub_category_id}, {"sub_categories.$": 1}
    )
    if category and "sub_categories" in category:
        return category["sub_categories"][0]["name"]
    return "Unknown Sub Category"


async def get_city_name(city_id: ObjectId) -> str:
    city = await motor_db.cities.find_one({"_id": city_id})
    return city["name"] if city else "Unknown City"
