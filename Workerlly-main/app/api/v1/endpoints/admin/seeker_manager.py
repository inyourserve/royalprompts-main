# app/api/v1/endpoints/admin/seeker_manager.py

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
MODULE = "seekers"
ACTIONS = {"VIEW": "read"}


@router.get("/seekers")
async def get_all_seekers(
    search: Optional[str] = Query(None, description="Search by name"),
    status: Optional[str] = Query(None, description="Filter by current status"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    city_id: Optional[str] = Query(None, description="Filter by city"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page"),
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        skip = (page - 1) * limit

        # Build base query
        query = {"seeker_stats": {"$exists": True}}

        # Add search filter
        if search:
            query["personal_info.name"] = {"$regex": search, "$options": "i"}

        # Add status filter
        if status and status != "all":
            query["seeker_stats.user_status.current_status"] = status

        # Add category filter
        if category_id and category_id != "all":
            query["seeker_stats.category.category_id"] = ObjectId(category_id)

        # Add city filter
        if city_id and city_id != "all":
            query["seeker_stats.city_id"] = ObjectId(city_id)

        # Get total count
        total_count = await motor_db.user_stats.count_documents(query)

        # Join with users collection to get mobile numbers
        pipeline = [
            {"$match": query},
            {"$sort": {"seeker_stats.total_jobs_done": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
            {"$unwind": "$user"},
        ]

        seekers = await motor_db.user_stats.aggregate(pipeline).to_list(length=limit)

        # Format seeker response
        formatted_seekers = []
        for seeker in seekers:
            personal_info = seeker.get("personal_info", {})
            seeker_stats = seeker.get("seeker_stats", {})
            user_status = seeker_stats.get("user_status", {})
            category = seeker_stats.get("category", {})

            formatted_seeker = {
                "id": str(seeker["user_id"]),
                "name": personal_info.get("name", ""),
                "mobile": seeker["user"].get("mobile", ""),
                "category": category.get("category_name", ""),
                "city": seeker_stats.get("city_name", ""),
                "current_status": user_status.get("current_status", ""),
                "total_jobs": seeker_stats.get("total_jobs_done", 0),
                "total_earned": seeker_stats.get("total_earned", 0),
            }
            formatted_seekers.append(formatted_seeker)

        # Get all active cities for filtering
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
            "data": formatted_seekers,
            "cities": cities,
            "categories": categories,
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": limit,
                "total_pages": (total_count + limit - 1) // limit,
            },
        }

    except PyMongoError as e:
        logger.error(f"Database error in get_all_seekers: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_seekers: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
