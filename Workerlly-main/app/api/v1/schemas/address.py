from datetime import datetime
from typing import Optional, Any, Dict

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, ObjectId):
            try:
                return ObjectId(v)
            except:
                raise ValueError("Invalid ObjectId")
        return v

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema

        return core_schema.json_or_python_schema(
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            json_schema=core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )


class AddressCreate(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    apartment_number: Optional[str] = None
    landmark: Optional[str] = None
    location: Dict[str, Any]  # GeoJSON Point object
    label: str
    address_type: Optional[str] = None


class AddressResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    address_line1: str
    address_line2: Optional[str] = None
    apartment_number: Optional[str] = None
    landmark: Optional[str] = None
    label: str
    address_type: Optional[str]
    location: dict
    city_id: str
    created_at: datetime
    updated_at: datetime
    # Add other fields as needed


class AddressUpdate(BaseModel):
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    apartment_number: Optional[str] = None
    landmark: Optional[str] = None
    label: Optional[str] = None
    address_type: Optional[str] = None
    location: Optional[dict] = None  # GeoJSON object
    city_id: Optional[PyObjectId] = Field(
        None, example="60b6a2c97b4e3f1a4cde1234"
    )  # Optional for updates

    class Config:
        arbitrary_types_allowed = True
