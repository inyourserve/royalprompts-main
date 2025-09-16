# from fastapi import HTTPException, Depends
#
# from app.api.v1.endpoints.users import get_current_user
#
#
# def role_required(required_role: str):
#     def role_checker(current_user: dict = Depends(get_current_user)):
#         if required_role not in current_user["roles"]:
#             raise HTTPException(
#                 status_code=403, detail="Operation not permitted for your role"
#             )
#         return current_user
#
#     return role_checker

from fastapi import HTTPException, Depends

from app.api.v1.endpoints.users import get_current_user


def role_required(required_roles: str):
    # Convert comma-separated string to list and clean whitespace
    roles = [role.strip() for role in required_roles.split(",")]

    def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user["roles"]
        # Check if user has any of the required roles
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=403, detail="Operation not permitted for your role"
            )
        return current_user

    return role_checker
