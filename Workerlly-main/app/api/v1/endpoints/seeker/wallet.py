import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.v1.endpoints.user_stats import update_user_stats
from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.wallet import WalletTransaction
from app.db.models.database import motor_db
from app.utils.nested_dict import get_nested_value
from app.utils.razorpay_utils import RazorpayUtils, RazorpayConfig
from app.utils.roles import role_required

router = APIRouter()

razorpay_config = RazorpayConfig(
    key_id="rzp_live_DBqXvgaIdpnYNz", key_secret="NgCUYG2cmhYfSJEoaamXa4Zd"
)

logger = logging.getLogger(__name__)


async def get_razorpay_utils():
    return RazorpayUtils(razorpay_config)


class RazorpayCallback(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


async def start_transaction():
    return await motor_db.client.start_session()


@router.post(
    "/wallet/initiate_recharge", dependencies=[Depends(role_required("seeker"))]
)
async def initiate_recharge(
    amount: float,
    current_user: dict = Depends(get_current_user),
    razorpay_utils: RazorpayUtils = Depends(get_razorpay_utils),
):
    try:
        user_id = ObjectId(current_user["user_id"])

        # Fetch user details from the users collection
        user = await motor_db.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        mobile_number = user.get("mobile")
        if not mobile_number:
            raise HTTPException(status_code=400, detail="User mobile number not found")

        async with await start_transaction() as session:
            async with session.start_transaction():
                order_data = {
                    "amount": int(amount * 100),  # Convert to paise
                    "currency": "INR",
                    "receipt": f"recharge_{user_id}",
                    "notes": {"mobile": mobile_number},
                }

                order = razorpay_utils.create_order(**order_data)

                payment_data = {
                    "user_id": user_id,
                    "amount": amount,
                    "status": "initiated",
                    "razorpay_order_id": order["id"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                result = await motor_db.payments.insert_one(
                    payment_data, session=session
                )

        logger.info(f"Recharge initiated for user {user_id}, amount: {amount}")
        return {
            "order_id": order["id"],
            "payment_id": str(result.inserted_id),
            "amount": amount,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error initiating recharge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate recharge")


@router.post(
    "/wallet/razorpay_callback", dependencies=[Depends(role_required("seeker"))]
)
async def razorpay_callback(
    callback: RazorpayCallback,
    razorpay_utils: RazorpayUtils = Depends(get_razorpay_utils),
):
    try:
        razorpay_utils.verify_payment_signature(
            callback.razorpay_order_id,
            callback.razorpay_payment_id,
            callback.razorpay_signature,
        )
    except Exception as e:
        logger.error(f"Invalid payment signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    async with await start_transaction() as session:
        async with session.start_transaction():
            payment = await motor_db.payments.find_one_and_update(
                {"razorpay_order_id": callback.razorpay_order_id},
                {
                    "$set": {
                        "status": "success",
                        "razorpay_payment_id": callback.razorpay_payment_id,
                        "updated_at": datetime.utcnow(),
                    }
                },
                return_document=True,
                session=session,
            )

            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")

            transaction_data = {
                "user_id": payment["user_id"],
                "amount": payment["amount"],
                "transaction_type": "credit",
                "description": "Wallet Recharge",
                "created_at": datetime.utcnow(),
            }
            await motor_db.transactions.insert_one(transaction_data, session=session)

            await update_user_stats(
                str(payment["user_id"]),
                {"seeker_stats.wallet_balance": payment["amount"]},
                session=session,
            )

    logger.info(
        f"Payment processed successfully for order {callback.razorpay_order_id}"
    )
    return {"status": "success", "message": "Payment processed successfully"}


@router.get(
    "/wallet/transactions/{user_id}", dependencies=[Depends(role_required("seeker"))]
)
async def get_transactions(user_id: str):
    try:
        transactions = (
            await motor_db.transactions.find({"user_id": ObjectId(user_id)})
            .sort("created_at", -1)
            .to_list(length=None)
        )

        for transaction in transactions:
            transaction["_id"] = str(transaction["_id"])
            transaction["user_id"] = str(transaction["user_id"])

        return {"transactions": transactions}
    except Exception as e:
        logger.error(f"Error fetching transactions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


@router.get(
    "/wallet/payments/{user_id}", dependencies=[Depends(role_required("seeker"))]
)
async def get_payments(user_id: str):
    try:
        payments = (
            await motor_db.payments.find({"user_id": ObjectId(user_id)})
            .sort("created_at", -1)
            .to_list(length=None)
        )

        for payment in payments:
            payment["_id"] = str(payment["_id"])
            payment["user_id"] = str(payment["user_id"])

        return {"payments": payments}
    except Exception as e:
        logger.error(f"Error fetching payments for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch payments")


@router.get("/wallet/balance", dependencies=[Depends(role_required("seeker"))])
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    try:
        # Extract user_id from the current authenticated user
        user_id = current_user["user_id"]

        # Fetch user stats from the user_stats collection
        user_stats = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
        if not user_stats:
            raise HTTPException(status_code=404, detail="User stats not found")

        # Use get_nested_value to get the wallet balance from seeker_stats
        wallet_balance = get_nested_value(
            user_stats, ["seeker_stats", "wallet_balance"], 0
        )

        return {"balance": wallet_balance}
    except Exception as e:
        logger.error(f"Error fetching wallet balance for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch wallet balance")


@router.get("/wallet/history", dependencies=[Depends(role_required("seeker"))])
async def get_wallet_history(current_user: dict = Depends(get_current_user)):
    try:
        user_id = ObjectId(current_user["user_id"])
        user_stats = await motor_db.user_stats.find_one({"user_id": user_id})
        if not user_stats:
            raise HTTPException(status_code=404, detail="User stats not found")

        wallet_balance = get_nested_value(
            user_stats, ["seeker_stats", "wallet_balance"], 0.0
        )

        transactions = (
            await motor_db.transactions.find({"user_id": user_id})
            .sort("created_at", -1)
            .to_list(None)
        )

        credit_transactions = []
        debit_transactions = []

        for transaction in transactions:
            wallet_transaction = WalletTransaction(
                transaction_id=str(transaction["_id"]),
                user_id=str(transaction["user_id"]),  # Convert ObjectId to string
                amount=transaction["amount"],
                transaction_type=transaction["transaction_type"],
                description=transaction.get("description"),
                created_at=transaction["created_at"],
            )
            if transaction["transaction_type"] == "credit":
                credit_transactions.append(wallet_transaction)
            else:
                debit_transactions.append(wallet_transaction)

        return {
            "wallet_balance": wallet_balance,
            "credit": [t.dict() for t in credit_transactions],
            "debit": [t.dict() for t in debit_transactions],
        }
    except Exception as e:
        logger.error(
            f"Error fetching wallet history for user {current_user['user_id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch wallet history")
