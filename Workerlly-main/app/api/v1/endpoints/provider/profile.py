from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.profile import ProviderProfileComplete
from app.db.models.database import db
from app.utils.roles import role_required

router = APIRouter()


@router.post(
    "/profile/complete",
    dependencies=[Depends(role_required("provider"))],
)
def complete_provider_profile(
    profile: ProviderProfileComplete,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Validate city ID and retrieve city name
    city = db.cities.find_one({"_id": ObjectId(profile.city_id)})
    if not city:
        raise HTTPException(status_code=400, detail="Invalid city ID")
    city_name = city.get("name")

    # Fetch existing user details
    existing_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare provider profile data for update in user_stats collection
    provider_profile_data = {
        "provider_stats.city_id": ObjectId(profile.city_id),
        "provider_stats.city_name": city_name,
    }

    # Update personal info
    personal_info_data = {
        "personal_info.name": profile.name,
    }

    # Update user_stats with new data
    db.user_stats.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": {**personal_info_data, **provider_profile_data}},
    )

    return {"message": "Profile updated successfully"}
