from typing import List, Optional
from fastapi import HTTPException, status

from app.services.base import BaseService
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteCreate, FavoriteWithPrompt
from app.db.base import MongoRepository


class FavoriteService(BaseService[Favorite, FavoriteCreate, dict]):
    """Favorite service for business logic"""
    
    def __init__(self):
        repository = MongoRepository(Favorite)
        super().__init__(repository)
    
    async def add_favorite(self, device_id: str, prompt_id: str) -> Favorite:
        """Add prompt to device favorites"""
        # Check if already favorited
        existing_favorite = await self.repository.find_one({
            "device_id": device_id,
            "prompt_id": prompt_id
        })
        
        if existing_favorite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt already in favorites"
            )
        
        favorite_data = {
            "device_id": device_id,
            "prompt_id": prompt_id
        }
        
        return await self.repository.create(favorite_data)
    
    async def remove_favorite(self, device_id: str, prompt_id: str) -> bool:
        """Remove prompt from device favorites"""
        favorite = await self.repository.find_one({
            "device_id": device_id,
            "prompt_id": prompt_id
        })
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        return await self.repository.delete(str(favorite.id))
    
    async def get_device_favorites(self, device_id: str) -> List[Favorite]:
        """Get all favorites for a device"""
        return await self.repository.find_many({"device_id": device_id})
    
    async def get_device_favorites_with_prompts(self, device_id: str) -> List[FavoriteWithPrompt]:
        """Get device favorites with prompt details"""
        from app.services.prompt_service import PromptService
        
        favorites = await self.get_device_favorites(device_id)
        prompt_service = PromptService()
        
        favorites_with_prompts = []
        for favorite in favorites:
            prompt = await prompt_service.get_by_id(favorite.prompt_id)
            if prompt:
                favorites_with_prompts.append(FavoriteWithPrompt(
                    id=str(favorite.id),
                    prompt=prompt,
                    created_at=favorite.created_at
                ))
        
        return favorites_with_prompts
    
    async def is_favorited(self, device_id: str, prompt_id: str) -> bool:
        """Check if prompt is favorited by device"""
        favorite = await self.repository.find_one({
            "device_id": device_id,
            "prompt_id": prompt_id
        })
        return favorite is not None
    
    async def get_prompt_favorites_count(self, prompt_id: str) -> int:
        """Get number of favorites for a prompt"""
        return await self.repository.count({"prompt_id": prompt_id})
    
    async def get_device_favorites_count(self, device_id: str) -> int:
        """Get number of favorites for a device"""
        return await self.repository.count({"device_id": device_id})
    
    async def get_popular_prompts_by_favorites(self, limit: int = 10) -> List[dict]:
        """Get most favorited prompts"""
        # This would typically use an aggregation pipeline
        # For now, we'll implement a simplified version
        from app.services.prompt_service import PromptService
        
        prompt_service = PromptService()
        all_prompts = await prompt_service.repository.find_many({})
        
        prompt_favorites = []
        for prompt in all_prompts:
            favorites_count = await self.get_prompt_favorites_count(str(prompt.id))
            prompt_favorites.append({
                "prompt": prompt,
                "favorites_count": favorites_count
            })
        
        # Sort by favorites count
        prompt_favorites.sort(key=lambda x: x["favorites_count"], reverse=True)
        
        return prompt_favorites[:limit]
    
    async def validate_create(self, favorite_in: FavoriteCreate) -> None:
        """Validate favorite creation"""
        # Check if prompt exists
        from app.services.prompt_service import PromptService
        
        prompt_service = PromptService()
        prompt = await prompt_service.get_by_id(favorite_in.prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found"
            )
    
    async def validate_update(self, favorite_id: str, favorite_in: dict) -> None:
        """Validate favorite update (not typically used)"""
        pass
