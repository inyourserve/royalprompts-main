from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.v1.schemas.salary import (
    SalaryCalculationRequest,
    SalaryCalculationResponse,
)
from app.db.models.database import db

router = APIRouter()


@router.post("/salary/calculate", response_model=SalaryCalculationResponse)
async def calculate_salary(request: SalaryCalculationRequest):
    # Check if the city is served
    city_data = db.cities.find_one({"_id": ObjectId(request.city_id)})
    if not city_data:
        raise HTTPException(
            status_code=404,
            detail="City not found",
        )

    if not city_data.get("is_served", False):
        raise HTTPException(
            status_code=400,
            detail=f"City '{city_data.get('name', 'Unknown')}' is not served",
        )

    # Fetch the rate for the given city_id and category_id
    rate_data = db.rates.find_one(
        {
            "city_id": ObjectId(request.city_id),
            "category_id": ObjectId(request.category_id),
        }
    )
    if not rate_data:
        raise HTTPException(
            status_code=404,
            detail="Rate not found for the given city and category",
        )

    # Calculate expected monthly income
    rate_per_hour = rate_data["rate_per_hour"]
    hours_per_day = request.hours_per_day
    days_per_month = request.days_per_month
    expected_monthly_income = rate_per_hour * hours_per_day * days_per_month

    return SalaryCalculationResponse(
        rate_per_hour=rate_per_hour,
        expected_monthly_income=expected_monthly_income,
    )
