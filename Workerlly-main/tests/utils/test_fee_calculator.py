from decimal import Decimal
from unittest.mock import patch

import pytest

from app.utils.fee_calculator import PlatformFeeCalculator, FeeBreakdown


@pytest.fixture(autouse=True)
def mock_settings():
    with patch("app.utils.fee_calculator.settings") as mock_settings:
        mock_settings.PLATFORM_FEE_PERCENTAGE = 20.0
        mock_settings.GST_PERCENTAGE = 18.0
        yield mock_settings


@pytest.fixture
def fee_calculator():
    """Fixture to create fee calculator instance"""
    return PlatformFeeCalculator()


class TestPlatformFeeCalculator:
    def test_round_amount(self, fee_calculator):
        """Test the _round_amount method"""
        test_cases = [
            (100.567, 100.57),
            (100.564, 100.56),
            (100.000, 100.00),
            (0.0, 0.00),
            (99.99999, 100.00),
        ]

        for input_amount, expected in test_cases:
            assert fee_calculator._round_amount(input_amount) == expected

    def test_calculate_fee(self, fee_calculator):
        """Test complete fee calculation"""
        test_cases = [
            {
                "hourly_rate": 500,
                "expected": {
                    "base_fee": 100.00,
                    "gst_amount": 18.00,
                    "total_fee": 118.00,
                    "hourly_rate": 500,
                    "fee_percentage": 20.0,
                    "gst_percentage": 18.0,
                },
            },
            {
                "hourly_rate": 1000,
                "expected": {
                    "base_fee": 200.00,
                    "gst_amount": 36.00,
                    "total_fee": 236.00,
                    "hourly_rate": 1000,
                    "fee_percentage": 20.0,
                    "gst_percentage": 18.0,
                },
            },
            {
                "hourly_rate": 0,
                "expected": {
                    "base_fee": 0.00,
                    "gst_amount": 0.00,
                    "total_fee": 0.00,
                    "hourly_rate": 0,
                    "fee_percentage": 20.0,
                    "gst_percentage": 18.0,
                },
            },
        ]

        for test_case in test_cases:
            result = fee_calculator.calculate_fee(test_case["hourly_rate"])
            assert result.model_dump() == test_case["expected"]

    def test_fee_breakdown_model(self, fee_calculator):
        """Test FeeBreakdown Pydantic model"""
        fee_data = {
            "base_fee": 100.00,
            "gst_amount": 18.00,
            "total_fee": 118.00,
            "hourly_rate": 500,
            "fee_percentage": 20.0,
            "gst_percentage": 18.0,
        }

        fee_breakdown = FeeBreakdown(**fee_data)
        assert fee_breakdown.model_dump() == fee_data

    @pytest.mark.parametrize("hourly_rate", [-100, 9999999, 0.01, 333.33])
    def test_edge_cases(self, fee_calculator, hourly_rate):
        """Test edge cases and boundary conditions"""
        result = fee_calculator.calculate_fee(hourly_rate)

        # Convert to Decimal for precise comparison
        base_fee = Decimal(str(result.base_fee))
        gst_amount = Decimal(str(result.gst_amount))
        total_fee = Decimal(str(result.total_fee))

        # Check if total_fee equals base_fee + gst_amount (within rounding tolerance)
        difference = abs(total_fee - (base_fee + gst_amount))
        assert difference <= Decimal(
            "0.01"
        ), f"Total fee difference ({difference}) exceeds tolerance"

    def test_decimal_precision(self, fee_calculator):
        """Test decimal precision handling"""
        test_cases = [333.33, 999999.99, 0.01, 1234567.89]

        for hourly_rate in test_cases:
            result = fee_calculator.calculate_fee(hourly_rate)

            # Verify decimal places
            assert (
                str(result.base_fee).split(".")[-1] <= "99"
            ), "Base fee has invalid decimal places"
            assert (
                str(result.gst_amount).split(".")[-1] <= "99"
            ), "GST amount has invalid decimal places"
            assert (
                str(result.total_fee).split(".")[-1] <= "99"
            ), "Total fee has invalid decimal places"

            # Verify rounding precision
            base_fee = Decimal(str(result.base_fee))
            gst_amount = Decimal(str(result.gst_amount))
            total_fee = Decimal(str(result.total_fee))

            assert abs(total_fee - (base_fee + gst_amount)) <= Decimal(
                "0.01"
            ), "Rounding error exceeds tolerance"
