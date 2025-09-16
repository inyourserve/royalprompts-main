from bson import ObjectId

from app.db.models.database import motor_db


async def fetch_user_mobile(user_id: str, role: str) -> str:
    """
    Fetch user's mobile number from users' collection.
    Args:
        user_id (str): User's ID as string
        role (str): Required role (provider/seeker)
    Returns:
        str: Mobile number or None if user_id is empty
    """
    if not user_id:  # If user_id is empty string
        return None

    try:
        user = await motor_db.users.find_one(
            {"_id": ObjectId(user_id), "roles": role}, {"mobile": 1}
        )
        if not user:
            return None  # Return None instead of raising exception

        return user["mobile"]
    except Exception:
        return None  # Return None for any error (invalid ID format etc)


# async def fetch_user_mobile(user_id: str, role: str) -> str:
#     """
#     Fetch user's mobile number from users' collection.
#
#     Args:
#         user_id (str): User's ID as string
#         role (str): Required role (provider/seeker)
#
#     Returns:
#         str: Mobile number
#
#     Raises:
#         HTTPException: If a user is not found, invalid ID or unauthorized role
#     """
#     try:
#         user = await motor_db.users.find_one(
#             {"_id": ObjectId(user_id), "roles": role}, {"mobile": 1}
#         )
#
#         if not user:
#             raise HTTPException(
#                 status_code=404, detail="User not found or unauthorized"
#             )
#
#         return user["mobile"]
#
#     except Exception as e:
#         raise HTTPException(status_code=400, detail="Invalid user ID format")
