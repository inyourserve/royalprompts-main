import uuid
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.s3_manager import upload_file_to_s3

router = APIRouter()


@router.patch(
    "/edit-profile",
    dependencies=[Depends(get_current_user)],
)
async def update_personal_info(
    name: str = Form(None),
    email: str = Form(None),
    gender: str = Form(None),
    dob: str = Form(None),
    marital_status: str = Form(None),
    religion: str = Form(None),
    diet: str = Form(None),
    profile_image: UploadFile = File(None),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    update_data = {}

    # Handle text fields
    if name is not None:
        update_data["personal_info.name"] = name
    if email is not None:
        update_data["personal_info.email"] = email
    if gender is not None:
        update_data["personal_info.gender"] = gender
    if dob is not None:
        update_data["personal_info.dob"] = datetime.fromisoformat(dob)
    if marital_status is not None:
        update_data["personal_info.marital_status"] = marital_status
    if religion is not None:
        update_data["personal_info.religion"] = religion
    if diet is not None:
        update_data["personal_info.diet"] = diet

    # Handle profile image upload
    if profile_image is not None:
        filename = f"{uuid.uuid4()}-{profile_image.filename}"
        s3_url = upload_file_to_s3(
            profile_image.file, f"public/profiles/{user_id}", filename
        )
        if not s3_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        update_data["personal_info.profile_image"] = s3_url

    # If there's nothing to update, return early
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Update personal info in user_stats collection
    result = await motor_db.user_stats.update_one(
        {"user_id": ObjectId(user_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="No changes made")

    return {"message": "Personal information updated successfully"}
