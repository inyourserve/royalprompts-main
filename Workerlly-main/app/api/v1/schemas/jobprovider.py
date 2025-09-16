from datetime import datetime
from typing import List, Optional, Any

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import core_schema


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(ObjectId),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )


class AddressSnapshot(BaseModel):
    id: PyObjectId = Field(alias="_id")
    address_line1: str
    address_line2: Optional[str] = None
    apartment_number: Optional[str] = None
    landmark: Optional[str] = None
    label: str
    address_type: Optional[str] = None
    location: dict
    city_id: PyObjectId
    type: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )


class HourlyRateUpdate(BaseModel):
    job_id: str
    new_hourly_rate: float


class HourlyRateEntry(BaseModel):
    rate: float
    updated_at: datetime


class JobCreate(BaseModel):
    category_id: PyObjectId
    sub_category_ids: List[PyObjectId]
    title: str
    description: str
    hourly_rate: float
    address_id: PyObjectId


class CancelJobResponse(BaseModel):
    message: str


class JobResponse(JobCreate):
    id: PyObjectId = Field(alias="_id")
    task_id: str
    user_id: PyObjectId
    current_rate: float
    hourly_rate_history: Optional[List[HourlyRateEntry]] = None
    address_snapshot: AddressSnapshot
    status: str
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
