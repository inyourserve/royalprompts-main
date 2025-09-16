import logging
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants for module and actions
MODULE = "reviews"
ACTIONS = {"VIEW": "read"}


@router.get("/reviews", response_model=List[dict])
async def get_reviews(
    search: Optional[str] = Query(None, description="Search by review or reviewer ID"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating"),
    reviewer_role: Optional[str] = Query(None, description="Filter by reviewer role"),
    skip: int = Query(0, ge=0, description="Number of reviews to skip for pagination"),
    limit: int = Query(
        10, gt=0, le=100, description="Maximum number of reviews to return"
    ),
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """
    Fetch reviews with optional searching and filtering for the admin panel.

    Parameters:
    - search (optional): Search for reviews by text or reviewer ID.
    - rating (optional): Filter reviews by rating.
    - reviewer_role (optional): Filter reviews by reviewer role.
    - skip (optional): Number of reviews to skip for pagination.
    - limit (optional): Maximum number of reviews to return.

    Returns:
    - List of reviews matching the search and filter criteria.
    """
    query = {}

    # Apply search filter
    if search:
        query["$or"] = [
            {"review": {"$regex": search, "$options": "i"}},  # Case-insensitive search
            {"reviewer_id": ObjectId(search) if ObjectId.is_valid(search) else None},
        ]

    # Apply rating filter
    if rating:
        query["rating"] = rating

    # Apply reviewer role filter
    if reviewer_role:
        query["reviewer_role"] = reviewer_role

    try:
        # Fetch reviews with optional pagination
        reviews_cursor = motor_db.reviews.find(query).skip(skip).limit(limit)
        reviews = await reviews_cursor.to_list(length=limit)

        # Convert ObjectId to string for `_id` and other fields
        for review in reviews:
            review["_id"] = str(review["_id"])
            review["job_id"] = str(review["job_id"])
            review["reviewer_id"] = str(review["reviewer_id"])
            review["reviewee_id"] = str(review["reviewee_id"])
            if "created_at" in review:
                review["created_at"] = review["created_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        return reviews

    except PyMongoError as e:
        logger.error(f"Failed to fetch reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reviews")
