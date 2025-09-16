from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

# Assuming PlatformFeeCalculator is already imported
from app.utils.platform_fee_calculator import get_fee_calculator, FeeBreakdown

router = APIRouter()


class HourlyRateRequest(BaseModel):
    hourly_rate: float


@router.post("/calculate-fee", response_model=FeeBreakdown)
def calculate_fee_endpoint(request: HourlyRateRequest):
    try:
        fee_calculator = get_fee_calculator()
        fee_breakdown = fee_calculator.calculate_fee(request.hourly_rate)
        return fee_breakdown
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
