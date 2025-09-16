from fastapi import Depends, HTTPException

from app.api.v1.dependencies.admin_auth import get_current_admin


async def check_admin_permission(user: dict, module: str, action: str) -> bool:
    """Check if user has permission for specific module and action"""
    try:
        # Get user's role and permissions
        role = user.get("role", {})

        # Debug print
        print(f"Checking permission - Module: {module}, Action: {action}")
        print(f"User Role Name: {role.get('name')}")
        print(f"User Permissions: {role.get('permissions')}")

        # If role name is super_admin, always allow
        if role.get("name") == "super_admin":
            return True

        # Check permissions
        permissions = role.get("permissions", [])
        for perm in permissions:
            if perm.get(
                "resource"
            ) == module and action in perm.get(  # Move operator to start of next line
                "actions", []
            ):
                return True

        return False
    except Exception as e:
        print(f"Error checking permissions: {e}")
        return False


def admin_permission_required(module: str, action: str):
    """Decorator to check admin permissions"""

    async def permission_checker(current_user: dict = Depends(get_current_admin)):
        has_permission = await check_admin_permission(current_user, module, action)
        if not has_permission:
            raise HTTPException(
                status_code=403, detail=f"No permission to {action} in {module}"
            )
        return current_user

    return permission_checker
