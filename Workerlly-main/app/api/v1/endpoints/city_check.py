from bson import ObjectId
from fastapi import APIRouter, Query

from app.api.v1.schemas.city_check import CityCheckResponse
from app.db.models.database import db

router = APIRouter()


@router.get("/city/check", response_model=CityCheckResponse)
async def check_city(
    city_id: str = Query(..., description="The ID of the city to check")
):
    # Check if the city is active based on the city_id
    city_data = db.cities.find_one({"_id": ObjectId(city_id), "status": "active"})
    if city_data:
        return CityCheckResponse(is_served=True)
    else:
        return CityCheckResponse(is_served=False)
    # mocked city_check
