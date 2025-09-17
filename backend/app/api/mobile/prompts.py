"""
Mobile App Prompts Endpoints
Handles prompt browsing, details, unlocking for mobile app
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.device_auth import get_authenticated_device_user
from app.schemas.prompt import PromptSummary, PromptDetail
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.prompt_service import PromptService
from app.services.favorite_service import FavoriteService

router = APIRouter()


# Guest browsing removed - anonymous login provides same functionality
@router.get("", response_model=PaginatedResponse[PromptSummary], tags=["Mobile Prompts"])
async def browse_prompts(
    category_id: Optional[str] = Query(None, description="Category ID to filter prompts"),
    search: Optional[str] = Query(None, description="Search term to filter prompts"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    device_user = Depends(get_authenticated_device_user)
):
    """
    Browse prompts - handles all mobile app tabs
    Supports filtering by category_id and search terms
    """
    prompt_service = PromptService()
    pagination = PaginationParams(skip=(page-1)*limit, limit=limit)
    
    if category_id:
        # Filter prompts by category ID
        prompts = await prompt_service.get_by_category(category_id, limit=limit)
        total = len(prompts)
    elif search:
        # Search prompts by search term
        prompts = await prompt_service.search(search, limit=limit)
        total = len(prompts)
    else:
        # Get all published prompts
        result = await prompt_service.get_multi(pagination, {"status": "published"})
        prompts = result.items
        total = result.total
    
    # Add unlock status for mobile app
    items_with_status = []
    for prompt in prompts:
        prompt_dict = prompt.model_dump()
        prompt_dict["id"] = str(prompt.id)
        prompt_dict["is_unlocked"] = device_user.has_unlocked_prompt(str(prompt.id))
        items_with_status.append(PromptSummary.model_validate(prompt_dict))
    
    return PaginatedResponse.create(items_with_status, total, pagination)


@router.get("/{prompt_id}", response_model=PromptDetail, tags=["Mobile Prompts"])
async def get_prompt_detail(
    prompt_id: str,
    device_user = Depends(get_authenticated_device_user)
):
    """Get prompt detail for mobile app prompt screen"""
    prompt_service = PromptService()
    favorite_service = FavoriteService()
    
    prompt = await prompt_service.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    is_unlocked = device_user.has_unlocked_prompt(prompt_id)
    is_favorited = await favorite_service.is_favorited(device_user.device_id, prompt_id)
    
    # Increment view count
    await prompt_service.increment_view(prompt_id)
    
    prompt_dict = prompt.model_dump()
    prompt_dict["id"] = str(prompt.id)
    prompt_dict["is_unlocked"] = is_unlocked
    prompt_dict["is_favorited"] = is_favorited
    
    return PromptDetail.model_validate(prompt_dict)


@router.post("/{prompt_id}/unlock", tags=["Mobile Prompts"])
async def unlock_prompt(
    prompt_id: str,
    device_user = Depends(get_authenticated_device_user)
):
    """Unlock premium prompt (matches 'Unlock to View Prompt' button)"""
    prompt_service = PromptService()
    
    prompt = await prompt_service.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    device_user.unlock_prompt(prompt_id)
    await device_user.save()
    
    return {"message": "Prompt unlocked successfully", "is_unlocked": True}
