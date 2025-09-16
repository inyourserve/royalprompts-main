# app/api/v1/endpoints/admin/roles_manager.py
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

router = APIRouter()

# Constants for module and actions
MODULE = "roles"
ACTIONS = {"VIEW": "read", "CREATE": "create", "UPDATE": "update", "DELETE": "delete"}


class PermissionModel(BaseModel):
    resource: str
    actions: List[str]


class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: List[PermissionModel]


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[PermissionModel]] = None


@router.get("/roles")
async def get_roles(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    try:
        roles = await motor_db.admin_roles.find().to_list(None)
        return {"data": [{**role, "_id": str(role["_id"])} for role in roles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles")
async def create_role(
    role: RoleCreate,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    try:
        # Check if role already exists
        if await motor_db.admin_roles.find_one({"name": role.name}):
            raise HTTPException(status_code=400, detail="Role already exists")

        role_doc = {
            "name": role.name,
            "description": role.description,
            "permissions": [perm.dict() for perm in role.permissions],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await motor_db.admin_roles.insert_one(role_doc)
        return {"id": str(result.inserted_id), "message": "Role created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    role: RoleUpdate,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    try:
        update_data = role.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        result = await motor_db.admin_roles.update_one(
            {"_id": ObjectId(role_id)}, {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Role not found")

        return {"message": "Role updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["DELETE"])),
):
    try:
        # Check if role is assigned to any users
        if await motor_db.admin_users.find_one({"roleId": ObjectId(role_id)}):
            raise HTTPException(
                status_code=400, detail="Cannot delete role as it is assigned to users"
            )

        result = await motor_db.admin_roles.delete_one({"_id": ObjectId(role_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Role not found")

        return {"message": "Role deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
