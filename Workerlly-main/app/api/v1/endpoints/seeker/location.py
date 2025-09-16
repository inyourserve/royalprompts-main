from bson import ObjectId
from fastapi import APIRouter, Depends

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.location import LocationUpdate
from app.db.models.database import db
from app.utils.roles import role_required

router = APIRouter()


@router.post(
    "/location/update",
    dependencies=[Depends(role_required("seeker"))],
)
async def update_location(
    location: LocationUpdate,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    db.user_stats.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$set": {
                "seeker_stats.location": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
            }
        },
    )

    return {"message": "Location updated successfully"}
