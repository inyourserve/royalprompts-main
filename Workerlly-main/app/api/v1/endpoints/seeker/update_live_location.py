from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.websocket_manager import manager

router = APIRouter()


@router.post("/update-live-location")
async def update_location(
    latitude: float,
    longitude: float,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(role_required("seeker")),
):
    user_id = ObjectId(current_user["user_id"])
    result = await update_seeker_location(user_id, latitude, longitude)
    if result:
        return {
            "message": "Location updated successfully",
            "job_id": result["job_id"],
            "sent_to_provider": result["sent_to_provider"],
        }
    else:
        raise HTTPException(status_code=400, detail="No active job found")


async def get_active_job_location(user_id: ObjectId) -> Optional[dict]:
    return await motor_db.active_job_locations.find_one(
        {"seeker_id": user_id, "status": "active"}
    )


async def update_seeker_location(
    user_id: ObjectId, latitude: float, longitude: float
) -> Optional[dict]:
    result = await motor_db.active_job_locations.find_one_and_update(
        {
            "seeker_id": user_id,
            "status": "active",
        },
        {
            "$set": {
                "seeker_location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "last_updated": datetime.utcnow(),
            }
        },
        return_document=True,
    )

    if not result:
        return None

    # Attempt to send the location update via WebSocket if the provider is tracking
    was_sent = await manager.send_location_update(
        str(result["job_id"]), latitude, longitude
    )

    return {"sent_to_provider": was_sent, "job_id": str(result["job_id"])}


async def handle_location_update(
    user_id: str, latitude: float, longitude: float
) -> dict:
    result = await update_seeker_location(ObjectId(user_id), latitude, longitude)
    if result:
        return {
            "type": "location_update_confirmation",
            "job_id": result["job_id"],
            "sent_to_provider": result["sent_to_provider"],
        }
    else:
        return {
            "type": "error",
            "message": "No active job found or failed to update location",
        }
