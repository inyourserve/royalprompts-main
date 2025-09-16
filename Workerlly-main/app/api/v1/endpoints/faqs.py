from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List
from app.db.models.database import db
from app.api.v1.schemas.faq import (
    FAQCategoryCreate,
    FAQCategoryResponse,
    FAQQuestionCreate,
    FAQQuestionResponse,
)

router = APIRouter()


def serialize_id(obj):
    if isinstance(obj, dict) and "_id" in obj:
        obj["_id"] = str(obj["_id"])
    if isinstance(obj, dict) and "category_id" in obj:
        obj["category_id"] = str(obj["category_id"])
    return obj


# FAQ Category Endpoints
@router.post("/faq/categories", response_model=FAQCategoryResponse)
def create_faq_category(category: FAQCategoryCreate):
    category_data = category.model_dump()
    result = db.faq_categories.insert_one(category_data)
    return FAQCategoryResponse(
        **serialize_id({"_id": result.inserted_id, **category_data})
    )


@router.get("/faq/categories", response_model=List[FAQCategoryResponse])
def list_faq_categories():
    categories = list(db.faq_categories.find())
    return [FAQCategoryResponse(**serialize_id(category)) for category in categories]


@router.patch("/faq/categories/{category_id}", response_model=FAQCategoryResponse)
def update_faq_category(category_id: str, category: FAQCategoryCreate):
    category_data = category.model_dump(exclude_unset=True)
    result = db.faq_categories.update_one(
        {"_id": ObjectId(category_id)}, {"$set": category_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    updated_category = db.faq_categories.find_one({"_id": ObjectId(category_id)})
    return FAQCategoryResponse(**serialize_id(updated_category))


@router.delete("/faq/categories/{category_id}")
def delete_faq_category(category_id: str):
    result = db.faq_categories.delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# FAQ Question Endpoints
@router.post("/faq/questions", response_model=FAQQuestionResponse)
def create_faq_question(question: FAQQuestionCreate):
    question_data = question.model_dump()
    question_data["category_id"] = ObjectId(question_data["category_id"])
    result = db.faq_questions.insert_one(question_data)
    created_question = db.faq_questions.find_one({"_id": result.inserted_id})
    return FAQQuestionResponse(**serialize_id(created_question))


@router.get("/faq/questions", response_model=List[FAQQuestionResponse])
def list_faq_questions(category_id: str):
    questions = list(db.faq_questions.find({"category_id": ObjectId(category_id)}))
    return [FAQQuestionResponse(**serialize_id(question)) for question in questions]


@router.patch("/faq/questions/{question_id}", response_model=FAQQuestionResponse)
def update_faq_question(question_id: str, question_update: FAQQuestionCreate):
    question_data = question_update.model_dump(exclude_unset=True)
    if "category_id" in question_data:
        question_data["category_id"] = ObjectId(question_data["category_id"])
    result = db.faq_questions.update_one(
        {"_id": ObjectId(question_id)}, {"$set": question_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    updated_question = db.faq_questions.find_one({"_id": ObjectId(question_id)})
    return FAQQuestionResponse(**serialize_id(updated_question))


@router.delete("/faq/questions/{question_id}")
def delete_faq_question(question_id: str):
    result = db.faq_questions.delete_one({"_id": ObjectId(question_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}
