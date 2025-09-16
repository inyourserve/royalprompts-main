from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache

from pydantic import BaseModel, Field

from app.core.config import settings


class FeeBreakdown(BaseModel):
    """Pydantic model for fee calculation response"""

    base_fee: float = Field(..., description="Base platform fee amount")
    gst_amount: float = Field(..., description="GST amount on base fee")
    total_fee: float = Field(..., description="Total fee including GST")
    hourly_rate: float = Field(..., description="Original hourly rate")
    # fee_percentage: float = Field(..., description="Platform fee percentage applied")
    # gst_percentage: float = Field(..., description="GST percentage applied")


class PlatformFeeCalculator:
    """Utility class for calculating platform fees"""

    def __init__(self):
        self.platform_fee_percentage = settings.PLATFORM_FEE_PERCENTAGE
        self.gst_percentage = settings.GST_PERCENTAGE

    def _round_amount(self, amount: float, decimal_places: int = 2) -> float:
        """Round amount to specified decimal places"""
        decimal_amount = Decimal(str(amount))
        return float(
            decimal_amount.quantize(
                Decimal(f'0.{"0" * decimal_places}'), rounding=ROUND_HALF_UP
            )
        )

    def calculate_fee(self, hourly_rate: float) -> FeeBreakdown:
        """Calculate complete fee breakdown"""
        # Convert to Decimal for precise calculation
        rate = Decimal(str(hourly_rate))
        fee_percent = Decimal(str(self.platform_fee_percentage)) / Decimal("100")
        gst_percent = Decimal(str(self.gst_percentage)) / Decimal("100")

        # Calculate fees
        base_fee = rate * fee_percent
        gst_amount = base_fee * gst_percent
        total_fee = base_fee + gst_amount

        # Round all amounts
        return FeeBreakdown(
            base_fee=self._round_amount(float(base_fee)),
            gst_amount=self._round_amount(float(gst_amount)),
            total_fee=self._round_amount(float(total_fee)),
            hourly_rate=float(rate),
        )


@lru_cache()
def get_fee_calculator() -> PlatformFeeCalculator:
    """Get or create singleton instance of PlatformFeeCalculator"""
    return PlatformFeeCalculator()
