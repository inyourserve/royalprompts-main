import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants for module and actions
MODULE = "rates"
ACTIONS = {"VIEW": "read", "CREATE": "create", "UPDATE": "update"}


class RateBase(BaseModel):
    """Base model for rate data"""

    city_id: str
    category_id: str
    rate_per_hour: float = Field(gt=0)
    min_hourly_rate: float = Field(gt=0)
    max_hourly_rate: float = Field(gt=0)

    @validator("max_hourly_rate")
    def validate_max_rate(cls, v, values):
        if "min_hourly_rate" in values and v < values["min_hourly_rate"]:
            raise ValueError("Maximum rate cannot be less than minimum rate")
        return v

    @validator("rate_per_hour")
    def validate_rate(cls, v, values):
        if all(k in values for k in ["min_hourly_rate", "max_hourly_rate"]):
            if not (values["min_hourly_rate"] <= v <= values["max_hourly_rate"]):
                raise ValueError("Rate must be between minimum and maximum rates")
        return v


@router.post("/rates")
async def create_or_update_rate(
    rate: RateBase,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    """Create or update a rate for a specific city and category"""
    try:
        # Validate city exists
        city = await motor_db.cities.find_one({"_id": ObjectId(rate.city_id)})
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

        # Validate category exists
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(rate.category_id)}
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        rate_data = {
            "city_id": ObjectId(rate.city_id),
            "category_id": ObjectId(rate.category_id),
            "rate_per_hour": rate.rate_per_hour,
            "min_hourly_rate": rate.min_hourly_rate,
            "max_hourly_rate": rate.max_hourly_rate,
            "updated_at": datetime.utcnow(),
        }

        # Check if rate already exists
        existing_rate = await motor_db.rates.find_one(
            {"city_id": rate_data["city_id"], "category_id": rate_data["category_id"]}
        )

        if existing_rate:
            # Update existing rate
            result = await motor_db.rates.update_one(
                {"_id": existing_rate["_id"]}, {"$set": rate_data}
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Failed to update rate")
            return {
                "success": True,
                "message": "Rate updated successfully",
                "rate_id": str(existing_rate["_id"]),
            }
        else:
            # Create new rate
            rate_data["created_at"] = datetime.utcnow()
            result = await motor_db.rates.insert_one(rate_data)
            return {
                "success": True,
                "message": "Rate created successfully",
                "rate_id": str(result.inserted_id),
            }

    except PyMongoError as e:
        logger.error(f"Database error in create_or_update_rate: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in create_or_update_rate: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/rates")
async def get_rates(
    city_id: Optional[str] = Query(None, description="Filter by city"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, gt=0, le=100, description="Items per page"),
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """Get paginated list of rates with optional filtering"""
    try:
        # Calculate skip for pagination
        skip = (page - 1) * per_page

        # Build base query
        query = {}
        if city_id and city_id != "all":
            query["city_id"] = ObjectId(city_id)
        if category_id and category_id != "all":
            query["category_id"] = ObjectId(category_id)

        # Get total count for pagination
        total_count = await motor_db.rates.count_documents(query)

        # Fetch rates with pagination
        cursor = (
            motor_db.rates.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        )

        rates = []
        async for rate in cursor:
            # Get city details
            city = await motor_db.cities.find_one({"_id": rate["city_id"]})
            city_name = city["name"] if city else "Unknown City"

            # Get category details
            category = await motor_db.categories.find_one({"_id": rate["category_id"]})
            category_name = category["name"] if category else "Unknown Category"

            # Prepare rate data
            rate_data = {
                "id": str(rate["_id"]),
                "city_id": str(rate["city_id"]),
                "city_name": city_name,
                "category_id": str(rate["category_id"]),
                "category_name": category_name,
                "rate_per_hour": rate["rate_per_hour"],
                "min_hourly_rate": rate["min_hourly_rate"],
                "max_hourly_rate": rate["max_hourly_rate"],
                "created_at": (
                    rate.get("created_at", "").isoformat()
                    if rate.get("created_at")
                    else None
                ),
                "updated_at": (
                    rate.get("updated_at", "").isoformat()
                    if rate.get("updated_at")
                    else None
                ),
            }
            rates.append(rate_data)

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
            "rates": rates,
            "cities": cities,
            "categories": categories,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
        }

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except PyMongoError as e:
        logger.error(f"Database error in get_rates: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_rates: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
