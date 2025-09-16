# admin/user_manager.py
import logging
from math import ceil
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants for module and actions
MODULE = "users"
ACTIONS = {"VIEW": "read", "UPDATE": "update"}


@router.get("/users")
async def get_all_users(
        search: Optional[str] = Query(None, description="Search by mobile number"),
        role: Optional[str] = Query(None, description="Filter by role"),
        status: Optional[str] = Query(None, description="Filter by status"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, gt=0, le=100, description="Items per page"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """
    Fetch all users with optional searching, filtering and page-based pagination.
    Parameters:
    - search (optional): Search for users by mobile number.
    - role (optional): Filter users by role.
    - status (optional): Filter users by status.
    - page (optional): Current page number (starts from 1).
    - page_size (optional): Number of items per page (default 10, max 100).
    Returns:
    - Paginated list of users with pagination metadata.
    """
    try:
        # Build query
        query = {}

        # Apply search filter
        if search:
            query["mobile"] = {"$regex": search, "$options": "i"}

        # Apply role filter
        if role:
            query["roles"] = role

        # Apply status filter
        if status:
            query["status"] = status

        # Calculate pagination values
        skip = (page - 1) * page_size

        # Get total count
        total_count = await motor_db.users.count_documents(query)

        # Calculate pagination metadata
        total_pages = ceil(total_count / page_size)
        has_next = page < total_pages
        has_previous = page > 1

        # Fetch users with pagination
        users_cursor = motor_db.users.find(query).skip(skip).limit(page_size)
        users = await users_cursor.to_list(length=page_size)

        # Format the users
        formatted_users = []
        for user in users:
            formatted_user = user.copy()
            formatted_user["_id"] = str(user["_id"])
            if "created_at" in formatted_user:
                formatted_user["created_at"] = formatted_user["created_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            formatted_users.append(formatted_user)

        # Prepare pagination metadata
        pagination = {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
            # Add page number list for UI pagination
            "pages": list(range(max(1, page - 2), min(total_pages + 1, page + 3))),
        }

        return {"data": formatted_users, "pagination": pagination}

    except PyMongoError as e:
        logger.error(f"Failed to fetch users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.put("/users/{user_id}/toggle-block")
async def toggle_user_block(
    user_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    """
    Toggle the block status of a user
    """
    try:
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user_obj_id = ObjectId(user_id)

        # Find the user
        user = await motor_db.users.find_one({"_id": user_obj_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Toggle the is_user_blocked status
        new_status = not user.get("is_user_blocked", False)

        # Update user document
        result = await motor_db.users.update_one(
            {"_id": user_obj_id}, {"$set": {"is_user_blocked": new_status}}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=400, detail="Failed to update user block status"
            )

        return {"status": "success", "is_blocked": new_status}

    except PyMongoError as e:
        logger.error(f"Database error while toggling user block status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update user block status"
        )


# Add these functions to user_manager.py


@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """
    Get detailed profile information for a user, including both provider and seeker stats if available
    """
    try:
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user_obj_id = ObjectId(user_id)

        # Get user base info
        user = await motor_db.users.find_one({"_id": user_obj_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user stats
        user_stats = await motor_db.user_stats.find_one({"user_id": user_obj_id})

        if not user_stats:
            raise HTTPException(status_code=404, detail="User stats not found")

        # Format the response
        user_profile = {
            "user_id": str(user["_id"]),
            "mobile": user["mobile"],
            "roles": user["roles"],
            "status": user["status"],
            "is_blocked": user.get("is_user_blocked", False),
            "created_at": user["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
            "personal_info": user_stats.get("personal_info", {}),
        }

        # Add provider stats if they exist
        if "provider_stats" in user_stats:
            provider_stats = user_stats["provider_stats"]
            if "city_id" in provider_stats:
                provider_stats["city_id"] = str(provider_stats["city_id"])
            user_profile["provider_stats"] = provider_stats

        # Add seeker stats if they exist
        if "seeker_stats" in user_stats:
            seeker_stats = user_stats["seeker_stats"]
            # Convert ObjectIds to strings
            if "city_id" in seeker_stats:
                seeker_stats["city_id"] = str(seeker_stats["city_id"])
            if "category" in seeker_stats:
                seeker_stats["category"]["category_id"] = str(
                    seeker_stats["category"]["category_id"]
                )
                if "sub_categories" in seeker_stats["category"]:
                    for sub_cat in seeker_stats["category"]["sub_categories"]:
                        sub_cat["_id"] = str(sub_cat["_id"])
            if (
                    "user_status" in seeker_stats
                    and "current_job_id" in seeker_stats["user_status"]
            ):
                seeker_stats["user_status"]["current_job_id"] = str(
                    seeker_stats["user_status"]["current_job_id"]
                )
            if "aadhar" in seeker_stats:
                seeker_stats["aadhar"] = str(seeker_stats["aadhar"])
            user_profile["seeker_stats"] = seeker_stats

        return user_profile

    except PyMongoError as e:
        logger.error(f"Database error while fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")
