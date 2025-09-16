import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants for module and actions
MODULE = "company_data"
ACTIONS = {"VIEW": "read", "CREATE": "create"}


@router.post("/company-data")
async def create_company_data(
    company_data: dict,
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    """
    Create a new company data entry.

    Parameters:
    - company_data: JSON body containing company details.

    Returns:
    - Success message and the inserted ID.
    """
    try:
        result = await motor_db.company_data.insert_one(company_data)
        return {
            "message": "Company data created successfully",
            "id": str(result.inserted_id),
        }

    except PyMongoError as e:
        logger.error(f"Failed to create company data: {e}")
        raise HTTPException(status_code=500, detail="Failed to create company data")


@router.get("/company-data", response_model=List[dict])
async def get_all_company_data(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """
    Fetch all company data entries.

    Returns:
    - List of all company data entries.
    """
    try:
        company_data_cursor = motor_db.company_data.find()
        company_data = await company_data_cursor.to_list(length=100)

        # Convert ObjectId to string for `_id`
        for data in company_data:
            data["_id"] = str(data["_id"])

        return company_data

    except PyMongoError as e:
        logger.error(f"Failed to fetch company data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company data")
