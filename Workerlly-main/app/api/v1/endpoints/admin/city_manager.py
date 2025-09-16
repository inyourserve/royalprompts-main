# admin/city_manager.py

from http.client import HTTPException
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.db.models.database import db
from app.utils.admin_roles import admin_permission_required

router = APIRouter()

# Constants for module and actions
MODULE = "cities"
ACTIONS = {"VIEW": "read", "CREATE": "create", "UPDATE": "update"}


class StateBase(BaseModel):
    name: str


class CityCreateRequest(BaseModel):
    name: str
    is_served: bool
    state_id: str


class CityCheckResponse(BaseModel):
    is_served: bool


class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/states")
def get_states(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """Get all states for the dropdown selection"""
    states = list(db.states.find({}, {"name": 1}))
    return {
        "states": [{"id": str(state["_id"]), "name": state["name"]} for state in states]
    }


@router.post("/cities", response_model=dict)
def create_city(
    city: CityCreateRequest,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    # Validate state exists
    state = db.states.find_one({"_id": ObjectId(city.state_id)})
    if not state:
        raise HTTPException(status_code=404, detail="State not found")

    # Check if city already exists in the same state
    existing_city = db.cities.find_one(
        {"name": city.name, "state_id": ObjectId(city.state_id)}
    )
    if existing_city:
        raise HTTPException(status_code=400, detail="City already exists in this state")

    # Create new city
    city_data = {
        "name": city.name,
        "is_served": city.is_served,
        "state_id": ObjectId(city.state_id),
    }

    city_id = db.cities.insert_one(city_data).inserted_id

    return {
        "success": True,
        "city_id": str(city_id),
        "message": "City created successfully",
    }


@router.get("/cities", response_model=PaginatedResponse)
async def get_cities(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        state_id: Optional[str] = None,
        is_served: Optional[bool] = None,
        search: Optional[str] = None,
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    # Build the match stage for filtering
    match_stage = {}
    if state_id:
        match_stage["state_id"] = ObjectId(state_id)
    if is_served is not None:
        match_stage["is_served"] = is_served
    if search:
        match_stage["name"] = {
            "$regex": search,
            "$options": "i",
        }  # Case-insensitive search

    # Build the aggregation pipeline
    pipeline = []

    # Only add match stage if there are filters
    if match_stage:
        pipeline.append({"$match": match_stage})

    # Add the rest of the pipeline stages
    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "states",
                    "localField": "state_id",
                    "foreignField": "_id",
                    "as": "state_info",
                }
            },
            {"$unwind": {"path": "$state_info", "preserveNullAndEmptyArrays": True}},
            {
                "$addFields": {
                    "sort_order": {"$cond": [{"$eq": ["$is_served", True]}, 0, 1]}
                }
            },
            {"$sort": {"sort_order": 1, "name": 1}},
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [{"$skip": (page - 1) * per_page}, {"$limit": per_page}],
                }
            },
        ]
    )

    # Execute aggregation
    result = list(db.cities.aggregate(pipeline))

    if not result or not result[0]["metadata"]:
        return PaginatedResponse(
            data=[], total=0, page=page, per_page=per_page, total_pages=0
        )

    total = result[0]["metadata"][0]["total"]
    cities = result[0]["data"]

    # Process the results
    for city in cities:
        city["_id"] = str(city["_id"])
        city["state_id"] = str(city["state_id"])
        city["state_name"] = city["state_info"].get("name", "Unknown")
        del city["state_info"]
        if "sort_order" in city:
            del city["sort_order"]

    return PaginatedResponse(
        data=cities,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=-(total // -per_page),  # Ceiling division
    )


@router.patch("/cities/{city_id}")
async def update_city_service_status(
    city_id: str,
    update_data: CityCheckResponse,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    try:
        result = db.cities.update_one(
            {"_id": ObjectId(city_id)}, {"$set": {"is_served": update_data.is_served}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="City not found")

        return {"success": True, "message": "City service status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
