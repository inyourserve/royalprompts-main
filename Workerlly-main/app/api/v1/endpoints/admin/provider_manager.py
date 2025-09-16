# app/api/v1/endpoints/admin/provider_manager.py

import logging
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants for module and actions
MODULE = "providers"
ACTIONS = {"VIEW": "read"}


@router.get("/providers")
async def get_all_providers(
    city_id: Optional[str] = Query(None, description="Filter by city"),
    status: Optional[str] = Query(None, description="Filter by block status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page"),
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """Get paginated list of providers with optional filtering"""
    try:
        skip = (page - 1) * limit

        # Build base pipeline for providers
        pipeline = [
            # Match users with provider role
            {"$match": {"roles": "provider"}}
        ]

        # Add block status filter if provided
        if status is not None:
            status_bool = status.lower() == "true"
            pipeline[0]["$match"]["is_user_blocked"] = status_bool

        # Join with user_stats to get provider details
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "user_stats",
                        "localField": "_id",
                        "foreignField": "user_id",
                        "as": "stats",
                    }
                },
                {"$unwind": "$stats"},
            ]
        )

        # Add city filter if provided
        if city_id and city_id != "all":
            pipeline.append(
                {"$match": {"stats.provider_stats.city_id": ObjectId(city_id)}}
            )

        # Get total count
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        count_result = await motor_db.users.aggregate(count_pipeline).to_list(length=1)
        total_count = count_result[0]["total"] if count_result else 0

        # Add pagination
        pipeline.extend([{"$skip": skip}, {"$limit": limit}])

        # Execute the pipeline
        providers = await motor_db.users.aggregate(pipeline).to_list(length=limit)

        # Get all active cities for filtering
        cities_cursor = motor_db.cities.find({"is_served": True})
        cities = await cities_cursor.to_list(length=None)
        cities_list = [
            {"id": str(city["_id"]), "name": city["name"]} for city in cities
        ]

        # Format response
        formatted_providers = []
        for provider in providers:
            stats = provider.get("stats", {})
            personal_info = stats.get("personal_info", {})
            provider_stats = stats.get("provider_stats", {})

            formatted_provider = {
                "id": str(provider["_id"]),
                "name": personal_info.get("name", ""),
                "mobile": provider.get("mobile", ""),
                "city": provider_stats.get("city_name", ""),
                "rating": provider_stats.get("avg_rating", 0),
                "total_jobs": provider_stats.get("total_jobs_completed", 0),
                "total_spent": provider_stats.get("total_spent", 0),
                "is_blocked": provider.get("is_user_blocked", False),
            }
            formatted_providers.append(formatted_provider)

        return {
            "data": formatted_providers,
            "cities": cities_list,
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": limit,
                "total_pages": (total_count + limit - 1) // limit,
            },
        }

    except PyMongoError as e:
        logger.error(f"Database error in get_all_providers: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_providers: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
