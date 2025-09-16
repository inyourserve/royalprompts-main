from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.profile import ProfileComplete
from app.db.models.database import db
from app.utils.roles import role_required

router = APIRouter()


@router.post(
    "/profile/complete",
    dependencies=[Depends(role_required("seeker"))],
)
def complete_profile(
    profile: ProfileComplete,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Validate category ID and retrieve category name
    category = db.categories.find_one({"_id": ObjectId(profile.category_id)})
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category ID")

    category_name = category.get("name")

    # Validate and retrieve subcategory names and nest them under sub_category_id
    sub_category_ids = []
    for sub_category_id in profile.sub_category_id:
        sub_category_obj_id = ObjectId(sub_category_id)
        sub_category = next(
            (
                sub
                for sub in category["sub_categories"]
                if sub["id"] == sub_category_obj_id
            ),
            None,
        )
        if not sub_category:
            raise HTTPException(
                status_code=400, detail=f"Invalid sub-category ID: {sub_category_id}"
            )
        sub_category_ids.append(
            {"_id": sub_category_obj_id, "sub_category_name": sub_category["name"]}
        )

    # Validate city ID and retrieve city name
    city = db.cities.find_one({"_id": ObjectId(profile.city_id)})
    if not city:
        raise HTTPException(status_code=400, detail="Invalid city ID")

    city_name = city.get("name")

    # Prepare seeker profile data for update in user_stats collection
    seeker_profile_data = {
        "seeker_stats.city_id": ObjectId(profile.city_id),
        "seeker_stats.city_name": city_name,
        "seeker_stats.category.category_id": ObjectId(profile.category_id),
        "seeker_stats.category.category_name": category_name,
        "seeker_stats.category.sub_categories": sub_category_ids,  # Nest subcategory names
        "seeker_stats.experience": profile.experience,
        "seeker_stats.aadhar": profile.aadhar,
    }

    # Update personal info if necessary (e.g., name)
    personal_info_data = {
        "personal_info.name": profile.name,
    }

    # Update user_stats with new data
    db.user_stats.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": {**personal_info_data, **seeker_profile_data}},
    )

    return {"message": "Profile updated successfully"}
