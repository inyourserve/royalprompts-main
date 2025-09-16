from pydantic import BaseModel


class SalaryCalculationRequest(BaseModel):
    category_id: str
    city_id: str
    hours_per_day: int
    days_per_month: int


class SalaryCalculationResponse(BaseModel):
    rate_per_hour: float
    expected_monthly_income: float
