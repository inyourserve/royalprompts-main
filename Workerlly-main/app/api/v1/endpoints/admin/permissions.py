# app/api/v1/endpoints/admin/permissions.py
from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.models.database import motor_db

router = APIRouter()


class PermissionCreate(BaseModel):
    module: str
    action: str
    roles: List[str]


class PermissionUpdate(BaseModel):
    module: Optional[str] = None
    action: Optional[str] = None
    roles: Optional[List[str]] = None


@router.get("/permissions")
async def get_permissions(search: Optional[str] = None):
    try:
        query = {}
        if search:
            query["$or"] = [
                {"module": {"$regex": search, "$options": "i"}},
                {"action": {"$regex": search, "$options": "i"}},
            ]

        cursor = motor_db.admin_permissions.find(query).sort(
            [("module", 1), ("action", 1)]
        )
        permissions = []

        async for permission in cursor:
            permissions.append(
                {
                    "id": str(permission["_id"]),
                    "module": permission["module"],
                    "action": permission["action"],
                    "roles": permission["roles"],
                    "created_at": (
                        permission.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
                        if permission.get("created_at")
                        else None
                    ),
                }
            )

        return {"data": permissions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/permissions")
async def create_permission(permission: PermissionCreate):
    try:
        # Check if permission already exists
        if await motor_db.admin_permissions.find_one(
            {"module": permission.module, "action": permission.action}
        ):
            raise HTTPException(status_code=400, detail="Permission already exists")

        # Create new permission
        new_permission = {
            "module": permission.module,
            "action": permission.action,
            "roles": permission.roles,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await motor_db.admin_permissions.insert_one(new_permission)

        # Return created permission
        created_permission = await motor_db.admin_permissions.find_one(
            {"_id": result.inserted_id}
        )
        return {
            "id": str(created_permission["_id"]),
            "module": created_permission["module"],
            "action": created_permission["action"],
            "roles": created_permission["roles"],
            "created_at": created_permission["created_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/permissions/{permission_id}")
async def update_permission(permission_id: str, permission: PermissionUpdate):
    try:
        # Check if permission exists
        existing_permission = await motor_db.admin_permissions.find_one(
            {"_id": ObjectId(permission_id)}
        )
        if not existing_permission:
            raise HTTPException(status_code=404, detail="Permission not found")

        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if permission.module is not None:
            update_data["module"] = permission.module
        if permission.action is not None:
            update_data["action"] = permission.action
        if permission.roles is not None:
            update_data["roles"] = permission.roles

        # Update permission
        await motor_db.admin_permissions.update_one(
            {"_id": ObjectId(permission_id)}, {"$set": update_data}
        )

        # Return updated permission
        updated_permission = await motor_db.admin_permissions.find_one(
            {"_id": ObjectId(permission_id)}
        )
        return {
            "id": str(updated_permission["_id"]),
            "module": updated_permission["module"],
            "action": updated_permission["action"],
            "roles": updated_permission["roles"],
            "updated_at": updated_permission["updated_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/permissions/{permission_id}")
async def delete_permission(permission_id: str):
    try:
        # Check if permission exists
        existing_permission = await motor_db.admin_permissions.find_one(
            {"_id": ObjectId(permission_id)}
        )
        if not existing_permission:
            raise HTTPException(status_code=404, detail="Permission not found")

        # Delete permission
        await motor_db.admin_permissions.delete_one({"_id": ObjectId(permission_id)})

        return {"message": "Permission deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
