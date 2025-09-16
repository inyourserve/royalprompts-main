"""
Mobile App Prompts Endpoints
Handles prompt browsing, details, unlocking for mobile app
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.device_auth import get_active_device_user
from app.schemas.prompt import PromptSummary, PromptDetail
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.prompt_service import PromptService
from app.services.favorite_service import FavoriteService

router = APIRouter()


# Guest browsing removed - anonymous login provides same functionality
@router.get("", response_model=PaginatedResponse[PromptSummary], tags=["Mobile Prompts"])
async def browse_prompts(
    category: Optional[str] = Query(None, description="new|trending|cinematic|portra"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    device_user = Depends(get_active_device_user)
):
    """
    Browse prompts - handles all mobile app tabs
    Maps to: New, Trending, Cinematic, Portra tabs in mobile UI
    """
    prompt_service = PromptService()
    pagination = PaginationParams(skip=(page-1)*limit, limit=limit)
    
    if category == "new":
        prompts = await prompt_service.get_recent(limit=limit)
        total = len(prompts)
    elif category == "trending":
        prompts = await prompt_service.get_trending(limit=limit)
        total = len(prompts)
    elif category in ["cinematic", "portra"]:
        # Get category by name first, then get prompts by category
        from app.services.category_service import CategoryService
        category_service = CategoryService()
        category_obj = await category_service.get_by_name(category)
        if category_obj:
            prompts = await prompt_service.get_by_category(str(category_obj.id), limit=limit)
            total = len(prompts)
        else:
            prompts = []
            total = 0
    else:
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
    device_user = Depends(get_active_device_user)
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
    device_user = Depends(get_active_device_user)
):
    """Unlock premium prompt (matches 'Unlock to View Prompt' button)"""
    prompt_service = PromptService()
    
    prompt = await prompt_service.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    device_user.unlock_prompt(prompt_id)
    await device_user.save()
    
    return {"message": "Prompt unlocked successfully", "is_unlocked": True}
