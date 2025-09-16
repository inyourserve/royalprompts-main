from typing import Dict, Any, Optional

import razorpay
from fastapi import HTTPException
from pydantic import BaseModel


class RazorpayConfig(BaseModel):
    key_id: str
    key_secret: str


class RazorpayUtils:
    def __init__(self, config: RazorpayConfig):
        self.client = razorpay.Client(auth=(config.key_id, config.key_secret))

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        prefill: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order.

        :param amount: Amount in the smallest currency unit (e.g., paise for INR)
        :param currency: Currency code (default is 'INR')
        :param receipt: Optional receipt id
        :param notes: Optional notes for the order
        :param prefill: Optional prefill information for the order
        :return: Razorpay order details
        """
        try:
            order_data = {
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "payment_capture": "1",  # Auto capture
            }
            if notes:
                order_data["notes"] = notes
            if prefill:
                order_data["prefill"] = prefill

            order = self.client.order.create(data=order_data)
            return order
        except razorpay.errors.BadRequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error creating Razorpay order: {str(e)}"
            )

    def verify_payment_signature(
        self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str
    ) -> bool:
        """
        Verify the Razorpay payment signature.

        :param razorpay_order_id: Razorpay order ID
        :param razorpay_payment_id: Razorpay payment ID
        :param razorpay_signature: Razorpay signature
        :return: True if signature is valid, False otherwise
        """
        try:
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    def capture_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """
        Capture a Razorpay payment.

        :param payment_id: Razorpay's payment ID
        :param amount: Amount to capture in the smallest currency unit
        :return: Captured payment details
        """
        try:
            return self.client.payment.capture(payment_id, int(amount * 100))
        except razorpay.errors.BadRequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error capturing payment: {str(e)}"
            )

    def refund_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """
        Refund a Razorpay payment.

        :param payment_id: Razorpay's payment ID
        :param amount: Amount to refund in the smallest currency unit
        :return: Refund details
        """
        try:
            return self.client.payment.refund(payment_id, int(amount * 100))
        except razorpay.errors.BadRequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error refunding payment: {str(e)}"
            )

    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Get details of a Razorpay payment.

        :param payment_id: Razorpay payment ID
        :return: Payment details
        """
        try:
            return self.client.payment.fetch(payment_id)
        except razorpay.errors.BadRequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching payment details: {str(e)}"
            )
