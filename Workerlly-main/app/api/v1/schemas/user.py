from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserSchema(BaseModel):
    mobile: str
    roles: List[str]


class Location(BaseModel):
    latitude: float
    longitude: float


class UserStatus(BaseModel):
    current_status: Optional[str] = None
    reason: Optional[str] = None
    current_job_id: Optional[str] = None
    status_updated_at: Optional[datetime] = None


class UserRead(BaseModel):
    id: str = Field(..., alias="_id")
    mobile: str
    roles: List[str]
    name: Optional[str] = None
    category_id: Optional[str] = None
    city_id: Optional[str] = None
    sub_category_id: Optional[List[str]] = []
    experience: Optional[int] = 0
    location: Optional[Location] = None


class UserWithStatus(BaseModel):
    user: UserRead
    user_status: UserStatus

    class Config:
        allow_population_by_name = True
        json_encoders = {ObjectId: str}
