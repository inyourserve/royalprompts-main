from datetime import datetime
from typing import Any, Literal

from bson import ObjectId
from pydantic import BaseModel, Field, constr


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


class ReviewCreate(BaseModel):
    job_id: PyObjectId
    rating: int = Field(..., ge=1, le=5)
    review: constr(strip_whitespace=True, min_length=1)


class ReviewResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    job_id: PyObjectId
    reviewer_id: PyObjectId
    reviewer_role: Literal["provider", "seeker"]
    rating: int = Field(..., ge=1, le=5)
    review: str
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True


class UserReviewStats(BaseModel):
    total_reviews_as_provider: int = Field(ge=0)
    total_reviews_as_seeker: int = Field(ge=0)
    avg_rating_as_provider: float = Field(ge=0, le=5)
    avg_rating_as_seeker: float = Field(ge=0, le=5)

    class Config:
        arbitrary_types_allowed = True
