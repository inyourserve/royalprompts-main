from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class LocationModel(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class BidBase(BaseModel):
    job_id: PyObjectId
    amount: float

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BidCreate(BaseModel):
    job_id: str  # Expect job_id as a string from the client
    amount: float


class BidUpdate(BaseModel):
    status: str


class SeekerInfo(BaseModel):
    name: str
    category: str
    current_location: LocationModel


class BidResponse(BaseModel):
    id: str = Field(alias="_id")
    job_id: str
    user_id: str
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @classmethod
    def from_mongo(cls, data: dict):
        if not data:
            return None
        return cls(
            _id=str(data["_id"]),
            job_id=str(data["job_id"]),
            user_id=str(data["user_id"]),
            amount=data["amount"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class BidDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    job_id: str
    seeker_id: str
    hourly_rate: float
    status: str
    seeker_info: SeekerInfo
    star_rating: float
    total_ratings: int
    estimated_time: int  # in minutes
    created_at: datetime

    class Config:
        allow_population_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BidListResponse(BaseModel):
    bids: List[BidDetailResponse]
    total: int


def bid_helper(bid) -> BidDetailResponse:
    return BidDetailResponse(
        _id=str(bid.get("_id", "")),
        job_id=str(bid.get("job_id", "")),
        seeker_id=str(bid.get("user_id", "")),
        hourly_rate=bid.get("amount", 0),
        status=bid.get("status", ""),
        seeker_info=SeekerInfo(
            name=bid["seeker_info"].get("name", ""),
            category=bid["seeker_info"].get("category", ""),
            current_location=LocationModel(
                **bid["seeker_info"].get("current_location", {})
            ),
        ),
        star_rating=bid.get("star_rating", 0),
        total_ratings=bid.get("total_ratings", 0),
        estimated_time=bid.get("estimated_time", 0),
        created_at=bid.get("created_at", datetime.utcnow()),
    )
