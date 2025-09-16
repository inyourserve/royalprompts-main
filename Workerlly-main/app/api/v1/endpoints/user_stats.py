from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClientSession

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.user_stat import UserStats
from app.db.models.database import motor_db

router = APIRouter()


@router.get("/user-stats/{user_id}", response_model=UserStats)
async def get_user_stats(user_id: str, current_user: dict = Depends(get_current_user)):
    user_stats = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
    if not user_stats:
        raise HTTPException(status_code=404, detail="User stats not found")

    # Convert ObjectId to string
    user_stats["user_id"] = str(user_stats["user_id"])
    if "seeker_stats" in user_stats and user_stats["seeker_stats"].get(
        "user_status", {}
    ).get("current_job_id"):
        user_stats["seeker_stats"]["user_status"]["current_job_id"] = str(
            user_stats["seeker_stats"]["user_status"]["current_job_id"]
        )

    return UserStats(**user_stats)


async def update_user_stats(
    user_id: str, update_data: dict, session: Optional[AsyncIOMotorClientSession] = None
):
    try:
        update_operation = {"$inc": update_data}
        if session:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)},
                update_operation,
                upsert=True,
                session=session,
            )
        else:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)}, update_operation, upsert=True
            )
    except Exception as e:
        # Log the error here
        raise HTTPException(
            status_code=500, detail=f"Failed to update user stats: {str(e)}"
        )


async def create_user_stats(
    user_id: str, roles: list, session: Optional[AsyncIOMotorClientSession] = None
):
    # Fetch existing user stats
    existing_stats = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})

    # Prepare the update operations without overwriting existing data
    update_data = {}

    # If no existing stats, initialize with personal info
    if not existing_stats:
        update_data["personal_info"] = {
            "name": None,  # Placeholder for user name
            "gender": None,
            "dob": None,
            "marital_status": None,
            "religion": None,
            "diet": None,
            "profile_image": "public/profiles/default.png",  # Default path
        }

    # Add provider_stats if a user is a provider, and it does not yet exist
    if "provider" in roles and (
        not existing_stats or "provider_stats" not in existing_stats
    ):
        update_data["provider_stats"] = {
            "city_id": None,
            "city_name": None,
            "total_jobs_posted": 0,
            "total_jobs_completed": 0,
            "total_jobs_cancelled": 0,
            "total_spent": 0,
            "total_reviews": 0,
            "avg_rating": 0,
            "sum_ratings": 0,
        }

    # Add seeker_stats if a user is a seeker, and it does not yet exist
    if "seeker" in roles and (
        not existing_stats or "seeker_stats" not in existing_stats
    ):
        update_data["seeker_stats"] = {
            "wallet_balance": 0.0,
            "city_id": None,
            "city_name": None,
            "category": {
                "category_id": None,
                "category_name": None,
                "sub_categories": [],
            },
            "location": {"latitude": None, "longitude": None},
            "experience": 0,
            "user_status": {
                "current_job_id": None,
                "current_status": "free",
                "reason": None,
                "status_updated_at": datetime.utcnow(),
            },
            "total_jobs_done": 0,
            "total_earned": 0,
            "total_hours_worked": 0,
            "total_reviews": 0,
            "avg_rating": 0,
            "sum_ratings": 0,
        }

    # If there's nothing to update, return early
    if not update_data:
        return

    try:
        # Insert a new user stats document if none exists or update the existing one with new role-specific stats
        if session:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)},
                {"$set": update_data},
                upsert=True,
                session=session,
            )
        else:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)}, {"$set": update_data}, upsert=True
            )
    except Exception as e:
        # Log the error here
        raise HTTPException(
            status_code=500, detail=f"Failed to create or update user stats: {str(e)}"
        )


async def update_user_status(
    user_id: str,
    status: str,
    reason: Optional[str] = None,
    job_id: Optional[str] = None,
    session: Optional[AsyncIOMotorClientSession] = None,
):
    update_data = {
        "seeker_stats.user_status.current_status": status,
        "seeker_stats.user_status.reason": reason,
        "seeker_stats.user_status.status_updated_at": datetime.utcnow(),
    }
    if job_id:
        update_data["seeker_stats.user_status.current_job_id"] = ObjectId(job_id)
    elif status == "free":
        update_data["seeker_stats.user_status.current_job_id"] = None

    try:
        if session:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)}, {"$set": update_data}, session=session
            )
        else:
            await motor_db.user_stats.update_one(
                {"user_id": ObjectId(user_id)}, {"$set": update_data}
            )
    except Exception as e:
        # Log the error here
        raise HTTPException(
            status_code=500, detail=f"Failed to update user status: {str(e)}"
        )


# This function should be called after user creation
async def initialize_user_stats(user_id: str, roles: list):
    await create_user_stats(user_id, roles)
