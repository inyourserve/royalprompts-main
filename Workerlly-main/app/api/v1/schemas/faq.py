from pydantic import BaseModel, Field
from typing import Optional


class FAQCategoryCreate(BaseModel):
    name: str
    role: str  # seeker or provider


class FAQCategoryResponse(FAQCategoryCreate):
    id: str = Field(alias="_id")


class FAQQuestionCreate(BaseModel):
    category_id: str
    question: str
    answer: Optional[str] = None


class FAQQuestionResponse(FAQQuestionCreate):
    id: str = Field(alias="_id")
