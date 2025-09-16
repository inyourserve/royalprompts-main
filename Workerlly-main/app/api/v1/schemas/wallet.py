from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class WalletTransaction(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str  # Changed from PyObjectId to str
    amount: float
    transaction_type: str  # "credit" or "debit"
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
