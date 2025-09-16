"""
Mobile App Categories Endpoints
Handles category listing for mobile app
"""
from fastapi import APIRouter

from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("", response_model=list[CategoryResponse], tags=["Mobile Categories"])
async def get_categories():
    """Get all active categories for mobile app"""
    category_service = CategoryService()
    categories = await category_service.get_active_categories()
    
    # Convert to response format
    category_responses = []
    for category in categories:
        category_dict = category.model_dump()
        category_dict["id"] = str(category.id)
        category_responses.append(CategoryResponse.model_validate(category_dict))
    
    return category_responses
