from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.status import StatusUpdateRequest
from app.db.models.database import motor_db
from app.utils.minimum_balance_required import (
    fetch_minimum_balance,
)  # Import the helper
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()


async def check_and_update_status(user_id: str) -> bool:
    """
    Check user's balance and update their status accordingly.
    Returns the current (potentially updated) status.
    """
    user_stats_doc = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
    if not user_stats_doc:
        raise HTTPException(status_code=404, detail="User stats not found")

    user_stats = extract_user_stats(user_stats_doc)
    wallet_balance = float(user_stats.get("seeker_stats", {}).get("wallet_balance", 0))

    # Fetch dynamic minimum balance required
    min_balance_required = await fetch_minimum_balance(user_id)

    user = await motor_db.users.find_one({"_id": ObjectId(user_id)}, {"status": 1})
    current_status = user.get("status", False)

    if wallet_balance < min_balance_required and current_status:
        # User's balance is below required minimum and they're online, set them offline
        await motor_db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"status": False}}
        )
        return False
    elif wallet_balance >= min_balance_required and not current_status:
        # User's balance meets the requirement but they need to explicitly go online
        return False
    else:
        # No change needed
        return current_status


@router.post("/status", dependencies=[Depends(role_required("seeker"))])
async def update_status(
    request: StatusUpdateRequest, current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    if request.status:
        # User is trying to go online, check their balance
        user_stats_doc = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(user_id)}
        )
        if not user_stats_doc:
            raise HTTPException(status_code=404, detail="User stats not found")

        wallet_balance = float(
            user_stats_doc.get("seeker_stats", {}).get("wallet_balance", 0)
        )

        # Fetch dynamic minimum balance required
        min_balance_required = await fetch_minimum_balance(user_id)

        if wallet_balance < min_balance_required:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance to go online. Minimum balance required: {min_balance_required}",
            )

    # Update the status
    await motor_db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"status": request.status}}
    )

    # Check and update status based on current balance
    final_status = await check_and_update_status(user_id)
    status_str = "online" if final_status else "offline"
    return {"message": f"Status updated to {status_str}"}


@router.get("/status", dependencies=[Depends(role_required("seeker"))])
async def get_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    # Check and update status based on current balance before returning
    current_status = await check_and_update_status(user_id)
    return {"status": current_status}


# from bson import ObjectId
# from fastapi import APIRouter, HTTPException, Depends
#
# from app.api.v1.endpoints.users import get_current_user
# from app.api.v1.schemas.status import StatusUpdateRequest
# from app.db.models.database import db
# from app.utils.roles import role_required
# from app.utils.user_stats_extractor import extract_user_stats
#
# router = APIRouter()
#
#
# def check_and_update_status(user_id: str) -> bool:
#     """
#     Check user's balance and update their status accordingly.
#     Returns the current (potentially updated) status.
#     """
#     user_stats_doc = db.user_stats.find_one({"user_id": ObjectId(user_id)})
#     if not user_stats_doc:
#         raise HTTPException(status_code=404, detail="User stats not found")
#
#     user_stats = extract_user_stats(user_stats_doc)
#     wallet_balance = float(user_stats.get("seeker_stats", {}).get("wallet_balance", 0))
#
#     current_status = db.users.find_one({"_id": ObjectId(user_id)}, {"status": 1})[
#         "status"
#     ]
#
#     if wallet_balance < 100.0 and current_status:
#         # User's balance is below 100 and they're currently online, set them offline
#         db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": False}})
#         return False
#     elif wallet_balance >= 100.0 and not current_status:
#         # User's balance is 100 or above and they're currently offline, keep them offline
#         # We don't automatically set users online, they need to do it explicitly
#         return False
#     else:
#         # No change needed
#         return current_status
#
#
# @router.post("/status", dependencies=[Depends(role_required("seeker"))])
# def update_status(
#         request: StatusUpdateRequest, current_user: dict = Depends(get_current_user)
# ):
#     user_id = current_user["user_id"]
#     if request.status:
#         # User is trying to go online, check their balance
#         user_stats_doc = db.user_stats.find_one({"user_id": ObjectId(user_id)})
#         if not user_stats_doc:
#             raise HTTPException(status_code=404, detail="User stats not found")
#
#         user_stats = extract_user_stats(user_stats_doc)
#         wallet_balance = float(
#             user_stats.get("seeker_stats", {}).get("wallet_balance", 0)
#         )
#
#         if wallet_balance < 100.0:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Insufficient balance to go online. Minimum balance required: 100",
#             )
#
#     # Update the status
#     db.users.update_one(
#         {"_id": ObjectId(user_id)}, {"$set": {"status": request.status}}
#     )
#
#     # Check and update status based on current balance
#     final_status = check_and_update_status(user_id)
#     status_str = "online" if final_status else "offline"
#     return {"message": f"Status updated to {status_str}"}
#
#
# @router.get("/status", dependencies=[Depends(role_required("seeker"))])
# def get_status(current_user: dict = Depends(get_current_user)):
#     user_id = current_user["user_id"]
#     # Check and update status based on current balance before returning
#     current_status = check_and_update_status(user_id)
#     return {"status": current_status}
