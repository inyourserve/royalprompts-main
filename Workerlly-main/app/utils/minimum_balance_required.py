from bson import ObjectId
from fastapi import HTTPException

from app.core.config import settings  # Import settings for platform fee and GST
from app.db.models.database import motor_db


async def fetch_minimum_balance(user_id: str) -> float:
    """
    Fetch the minimum balance required for a seeker to go online.

    Args:
        user_id (str): The ID of the user (seeker).

    Returns:
        float: The minimum balance required.
    """
    # Fetch user stats
    user_stats = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
    if not user_stats:
        raise HTTPException(status_code=404, detail="User stats not found")

    # Extract city_id and category_id from seeker_stats
    seeker_stats = user_stats.get("seeker_stats", {})
    city_id = seeker_stats.get("city_id")
    category_id = seeker_stats.get("category", {}).get("category_id")

    if not city_id or not category_id:
        raise HTTPException(
            status_code=400, detail="City ID or Category ID is missing in seeker stats"
        )

    # Fetch rate information from rates collection
    rate_data = await motor_db.rates.find_one(
        {"city_id": ObjectId(city_id), "category_id": ObjectId(category_id)}
    )
    if not rate_data:
        raise HTTPException(
            status_code=404,
            detail="Rate data not found for the given city and category",
        )

    min_hourly_rate = rate_data.get("min_hourly_rate", 0)
    if min_hourly_rate <= 0:
        raise HTTPException(status_code=400, detail="Invalid minimum hourly rate")

    # Get platform fee and GST from settings
    platform_fee_percentage = settings.PLATFORM_FEE_PERCENTAGE
    gst_percentage = settings.GST_PERCENTAGE

    # Calculate 20% of min_hourly_rate + GST
    platform_fee = (platform_fee_percentage / 100) * min_hourly_rate
    gst = (gst_percentage / 100) * platform_fee
    minimum_balance_required = platform_fee + gst

    return round(minimum_balance_required, 2)
