import logging
from datetime import datetime, timedelta
from typing import List
import jwt
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.endpoints.user_stats import create_user_stats
from app.api.v1.schemas.profile import ProviderProfileResponse, SeekerProfileResponse
from app.api.v1.schemas.user import UserSchema
from app.core.config import settings
from app.db.models.database import motor_db
from app.services.redis_service import get_redis_service
from app.utils.msg91 import send_otp, verify_otp
from app.utils.redis_manager import RedisManager, get_redis_manager
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

logger = logging.getLogger(__name__)

router = APIRouter()

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


class AuthRequest(BaseModel):
    mobile: str
    otp: str
    roles: List[str]


# Mock send_otp function
async def mock_send_otp(mobile: str):
    print(f"Mock OTP sent to {mobile}: 1234")
    return True


# Mock verify_otp function
async def mock_verify_otp(mobile: str, otp: str):
    if otp == "1234":
        print(f"OTP {otp} verified for mobile {mobile}")
        return True
    else:
        print(f"Invalid OTP {otp} for mobile {mobile}")
        return False


async def mock_verify_otp(mobile: str, otp: str):
    if otp == "1234":
        print(f"OTP {otp} verified for mobile {mobile}")
        return True
    else:
        print(f"Invalid OTP {otp} for mobile {mobile}")
        return False


async def create_user_and_stats(mobile: str, roles: List[str]):
    session = await motor_db.client.start_session()
    try:
        async with session.start_transaction():
            result = await motor_db.users.insert_one(
                {
                    "mobile": mobile,
                    "roles": list(set(roles)),
                    "status": settings.DEFAULT_USER_STATUS,
                    "created_at": datetime.utcnow(),
                    "provider_deleted_at": None,
                    "seeker_deleted_at": None,
                },
                session=session,
            )
            user_id = result.inserted_id
            await create_user_stats(str(user_id), roles, session=session)
        return user_id
    except PyMongoError as e:
        logger.error(f"Transaction failed: {e}")
        raise HTTPException(status_code=500, detail="User registration failed")
    finally:
        await session.end_session()


@router.post("/users/register")
async def register_user(user: UserSchema):
    if not await send_otp(user.mobile):  # for mock use mock_send_otp
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": "OTP sent to mobile"}


@router.post("/users/auth")
async def authenticate_user(auth_request: AuthRequest):
    mobile, otp, roles = auth_request.mobile, auth_request.otp, auth_request.roles
    if not await verify_otp(mobile, otp):  # for mock use mock_send_otp
        raise HTTPException(status_code=400, detail="Invalid OTP")

    query = {"mobile": mobile, "$and": [{f"{role}_deleted_at": None} for role in roles]}
    existing_user = await motor_db.users.find_one(query)

    if existing_user:
        user_id = existing_user["_id"]
        existing_roles = set(existing_user.get("roles", []))
        if not set(roles).issubset(existing_roles):
            updated_roles = list(existing_roles.union(roles))
            await motor_db.users.update_one(
                {"_id": user_id}, {"$set": {"roles": updated_roles}}
            )
            roles = updated_roles
            await create_user_stats(str(user_id), roles)
    else:
        user_id = await create_user_and_stats(mobile, roles)

    token = create_access_token(
        {"user_id": str(user_id), "mobile": mobile, "roles": roles}
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me/provider",
    response_model=ProviderProfileResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def get_provider_profile(
    current_user: dict = Depends(get_current_user),
    redis_manager: RedisManager = Depends(get_redis_manager),
):
    user_id = current_user["user_id"]
    object_id = ObjectId(user_id)

    # Fetch user details from user_stats collection
    user_details = await motor_db.user_stats.find_one({"user_id": object_id})
    if not user_details:
        raise HTTPException(status_code=401, detail="User stats not found")

    # Fetch from users collection for mobile and roles
    user_info = await motor_db.users.find_one({"_id": object_id})
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    # Get job_id from Redis using the simplified function
    redis_service = get_redis_service(redis_manager)
    job_idi = await redis_service.get_job_id_by_user_id(user_id)

    # Extract and process user stats
    user_stats = extract_user_stats(user_details)
    personal_info_data = user_stats.get("personal_info", {})
    provider_stats_data = user_stats.get("provider_stats", {})

    # Prepare the response data
    response_data = {
        "user_id": str(user_details["user_id"]),
        "mobile": user_info.get("mobile", ""),
        "personal_info": personal_info_data,
        "provider_stats": provider_stats_data,
        "job_id": job_idi,  # Will be either the job_id or None
    }

    return ProviderProfileResponse(**response_data)


@router.get(
    "/me/seeker",
    response_model=SeekerProfileResponse,
    dependencies=[Depends(role_required("seeker"))],
)
async def get_seeker_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    object_id = ObjectId(user_id)

    # Fetch user details from user_stats collection
    user_stats_doc = await motor_db.user_stats.find_one({"user_id": object_id})
    if not user_stats_doc:
        raise HTTPException(status_code=401, detail="User stats not found")

    # Fetch from users collection for mobile and roles
    user_info = await motor_db.users.find_one({"_id": object_id})
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract and process user stats
    user_stats = extract_user_stats(user_stats_doc)
    personal_info_data = user_stats.get("personal_info", {})
    seeker_stats_data = user_stats.get("seeker_stats", {})

    # Convert ObjectId to string for `city_id`, `category_id`, and other relevant fields
    if isinstance(seeker_stats_data.get("city_id"), ObjectId):
        seeker_stats_data["city_id"] = str(seeker_stats_data["city_id"])

    if isinstance(seeker_stats_data.get("category", {}).get("category_id"), ObjectId):
        seeker_stats_data["category"]["category_id"] = str(
            seeker_stats_data["category"]["category_id"]
        )

    if "sub_categories" in seeker_stats_data.get("category", {}):
        seeker_stats_data["category"]["sub_categories"] = [
            {
                "_id": str(sub_cat["_id"]),
                "sub_category_name": sub_cat.get("sub_category_name", ""),
            }
            for sub_cat in seeker_stats_data["category"].get("sub_categories", [])
        ]

    # Handle current_job_id in user_status
    if "user_status" in seeker_stats_data:
        if isinstance(seeker_stats_data["user_status"].get("current_job_id"), ObjectId):
            seeker_stats_data["user_status"]["current_job_id"] = str(
                seeker_stats_data["user_status"]["current_job_id"]
            )

    # Prepare the response data
    response_data = {
        "user_id": str(user_stats_doc["user_id"]),
        "mobile": user_info.get("mobile", ""),
        "roles": user_info.get("roles", []),
        "personal_info": personal_info_data,
        "seeker_stats": seeker_stats_data,
    }

    return SeekerProfileResponse(**response_data)


@router.post("/delete/provider")
async def delete_provider_role(current_user: dict = Depends(get_current_user)):
    user_id, roles = current_user["user_id"], current_user["roles"]
    if "provider" not in roles:
        raise HTTPException(
            status_code=400, detail="You don't have a provider role to delete"
        )
    updated_roles = [role for role in roles if role != "provider"]
    await motor_db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"provider_deleted_at": datetime.utcnow(), "roles": updated_roles}},
    )
    user = await motor_db.users.find_one({"_id": ObjectId(user_id)})
    fully_deleted = user.get("provider_deleted_at") and user.get("seeker_deleted_at")
    return {
        "success": True,
        "message": "Provider role deleted successfully",
        "fully_deleted": fully_deleted,
        "remaining_roles": updated_roles,
    }


@router.post("/delete/seeker")
async def delete_seeker_role(current_user: dict = Depends(get_current_user)):
    user_id, roles = current_user["user_id"], current_user["roles"]
    if "seeker" not in roles:
        raise HTTPException(
            status_code=400, detail="You don't have a seeker role to delete"
        )
    updated_roles = [role for role in roles if role != "seeker"]
    await motor_db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"seeker_deleted_at": datetime.utcnow(), "roles": updated_roles}},
    )
    user = await motor_db.users.find_one({"_id": ObjectId(user_id)})
    fully_deleted = user.get("provider_deleted_at") and user.get("seeker_deleted_at")
    return {
        "success": True,
        "message": "Seeker role deleted successfully",
        "fully_deleted": fully_deleted,
        "remaining_roles": updated_roles,
    }
