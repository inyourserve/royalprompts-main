"""
Mobile App Favorites Endpoints
Handles favorites management for mobile app
"""
from typing import List
from fastapi import APIRouter, Depends

from app.core.device_auth import get_authenticated_device_user
from app.schemas.prompt import PromptSummary
from app.services.favorite_service import FavoriteService

router = APIRouter()


@router.get("", response_model=List[PromptSummary], tags=["Mobile Favorites"])
async def get_favorites(device_user = Depends(get_authenticated_device_user)):
    """Get device's favorite prompts"""
    favorite_service = FavoriteService()
    favorites = await favorite_service.get_device_favorites_with_prompts(device_user.device_id)
    
    # Convert to response format
    favorite_prompts = []
    for fav in favorites:
        prompt_dict = fav.prompt.model_dump()
        prompt_dict["id"] = str(fav.prompt.id)
        favorite_prompts.append(PromptSummary.model_validate(prompt_dict))
    
    return favorite_prompts


@router.post("/{prompt_id}", tags=["Mobile Favorites"])
async def toggle_favorite(
    prompt_id: str,
    device_user = Depends(get_authenticated_device_user)
):
    """Toggle favorite status (heart icon in mobile UI)"""
    favorite_service = FavoriteService()
    
    is_favorited = await favorite_service.is_favorited(device_user.device_id, prompt_id)
    
    if is_favorited:
        await favorite_service.remove_favorite(device_user.device_id, prompt_id)
        return {"message": "Removed from favorites", "is_favorited": False}
    else:
        await favorite_service.add_favorite(device_user.device_id, prompt_id)
        return {"message": "Added to favorites", "is_favorited": True}
