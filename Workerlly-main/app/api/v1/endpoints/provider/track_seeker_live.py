from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.websocket_manager import manager

router = APIRouter()


@router.get("/track-seeker")
async def track_seeker(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(
        role_required("provider")
    ),  # Use role_required as a dependency injection
):
    user_id = ObjectId(current_user["user_id"])
    job_id_obj = ObjectId(job_id)

    # Fetch the active job location document
    active_job = await motor_db.active_job_locations.find_one(
        {"job_id": job_id_obj, "provider_id": user_id}
    )

    if not active_job:
        raise HTTPException(
            status_code=404,
            detail="Active job location not found or you're not authorized to track this job",
        )

    provider_location = active_job.get("provider_location", {}).get(
        "coordinates", [0, 0]
    )
    seeker_location = active_job.get("seeker_location", {}).get("coordinates", [0, 0])
    last_updated = active_job.get("last_updated", datetime.min)

    current_time = datetime.utcnow()
    is_online = (current_time - last_updated) <= timedelta(
        minutes=2
    )  # Consider offline if no update in 5 minutes

    # Start tracking for real-time updates
    manager.start_tracking(str(user_id), job_id)

    return {
        "provider_location": {
            "longitude": provider_location[0],
            "latitude": provider_location[1],
        },
        "seeker_location": {
            "longitude": seeker_location[0],
            "latitude": seeker_location[1],
        },
        "seeker_status": "online" if is_online else "offline",
        "last_updated": last_updated.isoformat(),
        "job_id": str(job_id_obj),
    }
