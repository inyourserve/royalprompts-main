# app/api/v1/endpoints/admin/auth.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.api.v1.endpoints.users import (
    mock_send_otp,
    mock_verify_otp,
    create_access_token,
)
from app.db.models.database import motor_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Request Models - Keeping same structure
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    mobile: str
    name: str
    roles: List[str]  # We'll use first role to get roleId


class VerifyRegisterRequest(BaseModel):
    mobile: str
    otp: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyLoginOTP(BaseModel):
    email: EmailStr
    otp: str


async def get_role_with_permissions(role_name: str):
    """Helper function to get role with permissions"""
    role = await motor_db.admin_roles.find_one({"name": role_name})
    if not role:
        return None
    return {"name": role["name"], "permissions": role["permissions"]}


@router.post("/register")
async def admin_register(request: RegisterRequest):
    # Check if email exists and verified
    existing_email = await motor_db.admin_users.find_one(
        {"email": request.email, "mobile_verified": True}
    )
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if mobile exists and verified
    existing_mobile = await motor_db.admin_users.find_one(
        {"mobile": request.mobile, "mobile_verified": True}
    )
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    try:
        # Get role from the first role in the list
        if not request.roles:
            raise HTTPException(status_code=400, detail="Role is required")

        role = await motor_db.admin_roles.find_one({"name": request.roles[0]})
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")

        # Check for existing unverified user
        existing_user = await motor_db.admin_users.find_one(
            {
                "$or": [
                    {"email": request.email, "mobile_verified": False},
                    {"mobile": request.mobile, "mobile_verified": False},
                ]
            }
        )

        if existing_user:
            # Update existing unverified user
            await motor_db.admin_users.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "email": request.email,
                        "password": pwd_context.hash(request.password),
                        "mobile": request.mobile,
                        "name": request.name,
                        "roleId": role["_id"],  # Store roleId
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        else:
            # Create new admin user
            admin_user = {
                "email": request.email,
                "password": pwd_context.hash(request.password),
                "mobile": request.mobile,
                "name": request.name,
                "roleId": role["_id"],  # Store roleId
                "status": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "mobile_verified": False,
            }
            await motor_db.admin_users.insert_one(admin_user)

        # Send OTP
        otp_sent = await mock_send_otp(request.mobile)
        if not otp_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP")

        return {
            "message": "OTP sent for verification",
            "mobile": f"{request.mobile[:3]}****{request.mobile[-4:]}",
            "status": "pending_verification",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-registration")
async def verify_admin_registration(request: VerifyRegisterRequest):
    # Find unverified admin
    admin = await motor_db.admin_users.find_one(
        {"mobile": request.mobile, "mobile_verified": False}
    )

    if not admin:
        raise HTTPException(
            status_code=404, detail="User not found or already verified"
        )

    # Verify OTP
    is_valid = await mock_verify_otp(request.mobile, request.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    try:
        # Get role info
        role = await motor_db.admin_roles.find_one({"_id": admin["roleId"]})
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")

        # Update admin status
        await motor_db.admin_users.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {
                    "status": True,
                    "mobile_verified": True,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return {
            "message": "Registration completed successfully",
            "user": {
                "id": str(admin["_id"]),
                "email": admin["email"],
                "name": admin["name"],
                "mobile": f"{admin['mobile'][:3]}****{admin['mobile'][-4:]}",
                "role": {"name": role["name"], "permissions": role["permissions"]},
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def admin_login(request: LoginRequest):
    # Find user and ensure they're verified
    admin = await motor_db.admin_users.find_one(
        {"email": request.email, "mobile_verified": True}
    )

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found or not verified")

    # Verify password
    if not pwd_context.verify(request.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Send OTP
    otp_sent = await mock_send_otp(admin["mobile"])
    if not otp_sent:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

    return {
        "message": "OTP sent successfully",
        "email": admin["email"],
        "mobile": f"{admin['mobile'][:3]}****{admin['mobile'][-4:]}",
        "status": "pending_verification",
    }


# Fixed verify-login endpoint
@router.post("/verify-login")
async def verify_admin_login(request: VerifyLoginOTP):
    try:
        # Find verified admin
        admin = await motor_db.admin_users.find_one(
            {"email": request.email, "mobile_verified": True}
        )

        if not admin:
            raise HTTPException(
                status_code=404, detail="Admin not found or not verified"
            )

        # Verify OTP
        is_valid = await mock_verify_otp(admin["mobile"], request.otp)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Get role with permissions
        role = await motor_db.admin_roles.find_one({"_id": admin.get("roleId")})
        if not role:
            # For backward compatibility, try to get role by name if roleId is not present
            role = await motor_db.admin_roles.find_one(
                {"name": admin.get("roles", ["viewer"])[0]}
            )
            if not role:
                raise HTTPException(status_code=400, detail="Role not found")

            # Update user with roleId if missing
            await motor_db.admin_users.update_one(
                {"_id": admin["_id"]}, {"$set": {"roleId": role["_id"]}}
            )

        # Update last login
        await motor_db.admin_users.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Generate access token
        access_token = create_access_token(
            data={
                "user_id": str(admin["_id"]),
                "email": admin["email"],
                "role": {
                    "name": role["name"],
                    "permissions": role.get("permissions", []),
                },
            }
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(admin["_id"]),
                "email": admin["email"],
                "name": admin["name"],
                "mobile": f"{admin['mobile'][:3]}****{admin['mobile'][-4:]}",
                "role": {
                    "name": role["name"],
                    "permissions": role.get("permissions", []),
                },
            },
        }

    except Exception as e:
        print(f"Login verification error: {str(e)}")  # For debugging
        raise HTTPException(status_code=500, detail="Login verification failed")
