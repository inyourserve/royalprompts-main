from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException

from app.api.v1.schemas.city_check import CityCheckResponse
from app.db.models.database import db

router = APIRouter()


# Function to convert ObjectId to string in the whole document
def convert_objectid_to_str(document):
    if not document:
        return document
    document["_id"] = str(document["_id"])
    if "state_id" in document and isinstance(document["state_id"], ObjectId):
        document["state_id"] = str(document["state_id"])
    return document


@router.get("/cities")
def get_cities():
    cities = list(db.cities.find({}))
    cities = [convert_objectid_to_str(city) for city in cities]  # Convert all ObjectIds
    return {"cities": cities}


@router.patch("/cities/{city_id}")
def update_city_service_status(city_id: str, update: CityCheckResponse):
    result = db.cities.update_one(
        {"_id": ObjectId(city_id)}, {"$set": {"is_served": update.is_served}}
    )
    if result.modified_count == 1:
        return {"success": True, "message": "City service status updated successfully"}
    else:
        raise HTTPException(
            status_code=404, detail="City not found or status unchanged"
        )


@router.get("/city/check", response_model=CityCheckResponse)
async def check_city(
    city_id: str = Query(..., description="The ID of the city to check")
):
    city_data = db.cities.find_one({"_id": ObjectId(city_id), "is_served": True})
    if city_data:
        return CityCheckResponse(is_served=True)
    else:
        return CityCheckResponse(is_served=False)
    # mock city checked


@router.delete("/cities/{city_id}")
def delete_city(city_id: str):
    result = db.cities.delete_one({"_id": ObjectId(city_id)})
    if result.deleted_count == 1:
        return {"success": True, "message": "City deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="City not found")
