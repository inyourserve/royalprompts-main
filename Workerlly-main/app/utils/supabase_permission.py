# app/utils/supabase_permission.py
from fastapi import Depends, HTTPException

from app.api.v1.dependencies.supabase_auth import verify_supabase_token


def admin_permission_required(resource: str, action: str):
    async def permission_dependency(user=Depends(verify_supabase_token)):
        permissions = user.get("permissions", [])

        print(user)

        allowed = any(
            perm["resource"] == resource and action in perm["actions"]
            for perm in permissions
        )

        if not allowed:
            raise HTTPException(status_code=403, detail="Permission denied")

        return user  # Optional: return user info to route if needed

    return permission_dependency
