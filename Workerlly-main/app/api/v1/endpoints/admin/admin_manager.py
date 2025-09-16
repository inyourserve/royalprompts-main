# app/api/v1/endpoints/admin/admin_manager.py
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Depends
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constants for module and actions
MODULE = "admins"
ACTIONS = {"VIEW": "read", "CREATE": "create", "UPDATE": "update", "DELETE": "delete"}


# Request models
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str
    roleId: str
    status: bool = True


router = APIRouter()


@router.get("/admins")
async def list_admin_users(
        search: Optional[str] = Query(None, description="Search by name, email or mobile"),
        status: Optional[bool] = Query(None, description="Filter by status"),
        roleId: Optional[str] = Query(None, description="Filter by roleId"),
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(10, gt=0, le=100, description="Number of records to return"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        # Build base query
        query = {"mobile_verified": True}  # Only show verified users

        # Apply search filter
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"mobile": {"$regex": search, "$options": "i"}},
            ]

        # Apply status filter
        if status is not None:
            query["status"] = status

        # Apply role filter
        if roleId:
            try:
                query["roleId"] = ObjectId(roleId)
            except:
                raise HTTPException(status_code=400, detail="Invalid roleId format")

        # Get total count
        total = await motor_db.admin_users.count_documents(query)

        # Fetch users with pagination
        cursor = (
            motor_db.admin_users.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        # Format response
        users = []
        async for user in cursor:
            # Get role details
            role = None
            if "roleId" in user:
                role = await motor_db.admin_roles.find_one({"_id": user["roleId"]})

            users.append(
                {
                    "id": str(user["_id"]),
                    "name": user["name"],
                    "email": user["email"],
                    "mobile": f"{user['mobile'][:3]}****{user['mobile'][-4:]}",
                    "roleId": str(user.get("roleId", "")),
                    "roleName": role["name"] if role else None,
                    "status": user.get("status", True),
                    "mobile_verified": user.get("mobile_verified", False),
                    "created_at": (
                        user.get("created_at").isoformat()
                        if user.get("created_at")
                        else None
                    ),
                    "last_login": (
                        user.get("last_login").isoformat()
                        if user.get("last_login")
                        else None
                    ),
                    "updated_at": (
                        user.get("updated_at").isoformat()
                        if user.get("updated_at")
                        else None
                    ),
                }
            )

        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "results": users,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch admin users: {str(e)}"
        )


@router.post("/admins")
async def create_admin(
    admin: AdminCreate,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    try:
        # Check if email already exists
        if await motor_db.admin_users.find_one({"email": admin.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if mobile already exists
        if await motor_db.admin_users.find_one({"mobile": admin.mobile}):
            raise HTTPException(
                status_code=400, detail="Mobile number already registered"
            )

        # Validate roleId
        try:
            role_id = ObjectId(admin.roleId)
            role = await motor_db.admin_roles.find_one({"_id": role_id})
            if not role:
                raise HTTPException(status_code=400, detail="Invalid role ID")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid role ID format")

        # Create new admin document
        new_admin = {
            "name": admin.name,
            "email": admin.email,
            "mobile": admin.mobile,
            "password": pwd_context.hash(admin.password),
            "roleId": role_id,
            "status": admin.status,
            "mobile_verified": True,  # Since we're creating from admin panel
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
        }

        # Insert the new admin
        result = await motor_db.admin_users.insert_one(new_admin)

        # Get the created admin
        created_admin = await motor_db.admin_users.find_one({"_id": result.inserted_id})

        # Get role details
        role = await motor_db.admin_roles.find_one({"_id": created_admin["roleId"]})

        # Return formatted response
        return {
            "id": str(created_admin["_id"]),
            "name": created_admin["name"],
            "email": created_admin["email"],
            "mobile": f"{created_admin['mobile'][:3]}****{created_admin['mobile'][-4:]}",
            "roleId": str(created_admin["roleId"]),
            "roleName": role["name"] if role else None,
            "status": created_admin["status"],
            "mobile_verified": created_admin["mobile_verified"],
            "created_at": created_admin["created_at"].isoformat(),
            "updated_at": created_admin["updated_at"].isoformat(),
            "last_login": None,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create admin: {str(e)}")


@router.get("/admins/{admin_id}")
async def get_admin(
    admin_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(admin_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid admin ID format")

    try:
        user = await motor_db.admin_users.find_one({"_id": object_id})
        if not user:
            raise HTTPException(status_code=404, detail="Admin not found")

        # Get role details
        role = None
        if "roleId" in user:
            role = await motor_db.admin_roles.find_one({"_id": user["roleId"]})

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "mobile": f"{user['mobile'][:3]}****{user['mobile'][-4:]}",
            "roleId": str(user.get("roleId", "")),
            "roleName": role["name"] if role else None,
            "status": user.get("status", True),
            "mobile_verified": user.get("mobile_verified", False),
            "created_at": (
                user.get("created_at").isoformat() if user.get("created_at") else None
            ),
            "last_login": (
                user.get("last_login").isoformat() if user.get("last_login") else None
            ),
            "updated_at": (
                user.get("updated_at").isoformat() if user.get("updated_at") else None
            ),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin: {str(e)}")


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["DELETE"])),
):
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(admin_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid admin ID format")

    try:
        # Check if admin exists
        admin = await motor_db.admin_users.find_one({"_id": object_id})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        # Get role to check if super admin
        if "roleId" in admin:
            role = await motor_db.admin_roles.find_one({"_id": admin["roleId"]})
            if role and role["name"] == "super_admin":
                raise HTTPException(status_code=400, detail="Cannot delete super admin")

        # Delete admin
        result = await motor_db.admin_users.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Admin not found")

        return {"message": "Admin deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete admin: {str(e)}")


# Add this model
class AdminUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    roleId: Optional[str] = None
    status: Optional[bool] = None


@router.put("/admins/{admin_id}")
async def update_admin(
    admin_id: str,
    admin_data: AdminUpdate,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(admin_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid admin ID format")

    try:
        # Check if admin exists
        existing_admin = await motor_db.admin_users.find_one({"_id": object_id})
        if not existing_admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        # Prepare update data
        update_data = {k: v for k, v in admin_data.dict().items() if v is not None}

        # Convert roleId to ObjectId if provided
        if "roleId" in update_data:
            try:
                update_data["roleId"] = ObjectId(update_data["roleId"])
                # Validate role exists
                role = await motor_db.admin_roles.find_one({"_id": update_data["roleId"]})
                if not role:
                    raise HTTPException(status_code=400, detail="Invalid role ID")
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid role ID format")

        # Check if email is being updated and is not already taken
        if "email" in update_data and update_data["email"] != existing_admin["email"]:
            if await motor_db.admin_users.find_one({"email": update_data["email"], "_id": {"$ne": object_id}}):
                raise HTTPException(status_code=400, detail="Email already registered")

        # Check if mobile is being updated and is not already taken
        if "mobile" in update_data and update_data["mobile"] != existing_admin["mobile"]:
            if await motor_db.admin_users.find_one({"mobile": update_data["mobile"], "_id": {"$ne": object_id}}):
                raise HTTPException(status_code=400, detail="Mobile number already registered")

        # Add timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Update admin
        await motor_db.admin_users.update_one(
            {"_id": object_id}, {"$set": update_data}
        )

        # Get updated admin
        updated_admin = await motor_db.admin_users.find_one({"_id": object_id})

        # Get role details
        role = None
        if "roleId" in updated_admin:
            role = await motor_db.admin_roles.find_one({"_id": updated_admin["roleId"]})

        # Return formatted response
        return {
            "id": str(updated_admin["_id"]),
            "name": updated_admin["name"],
            "email": updated_admin["email"],
            "mobile": f"{updated_admin['mobile'][:3]}****{updated_admin['mobile'][-4:]}",
            "roleId": str(updated_admin.get("roleId", "")),
            "roleName": role["name"] if role else None,
            "status": updated_admin.get("status", True),
            "mobile_verified": updated_admin.get("mobile_verified", False),
            "created_at": (
                updated_admin.get("created_at").isoformat()
                if updated_admin.get("created_at")
                else None
            ),
            "last_login": (
                updated_admin.get("last_login").isoformat()
                if updated_admin.get("last_login")
                else None
            ),
            "updated_at": (
                updated_admin.get("updated_at").isoformat()
                if updated_admin.get("updated_at")
                else None
            ),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update admin: {str(e)}"
        )
