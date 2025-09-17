from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime

from app.services.base import BaseService
from app.models.prompt import Prompt, PromptStatus
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptFilter
from app.db.base import MongoRepository


class PromptService(BaseService[Prompt, PromptCreate, PromptUpdate]):
    """Prompt service for business logic"""
    
    def __init__(self):
        repository = MongoRepository(Prompt)
        super().__init__(repository)
    
    async def create_prompt(self, prompt_in: PromptCreate, created_by: Optional[str] = None) -> Prompt:
        """Create a new prompt"""
        await self.validate_create(prompt_in)
        
        prompt_data = prompt_in.dict()
        prompt_data["created_by"] = created_by
        prompt_data["slug"] = self._generate_slug(prompt_in.title)
        
        return await self.repository.create(prompt_data)
    
    async def get_by_slug(self, slug: str) -> Optional[Prompt]:
        """Get prompt by slug"""
        return await self.repository.find_one({"slug": slug})
    
    async def get_by_category(self, category_id: str, limit: int = 20) -> List[Prompt]:
        """Get prompts by category"""
        return await self.repository.find_many({
            "category_id": category_id,
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }, limit=limit)
    
    # Removed get_by_type method since PromptType enum was removed
    
    async def get_featured(self, limit: int = 10) -> List[Prompt]:
        """Get featured prompts"""
        return await self.get_by_filter({
            "is_featured": True,
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }, limit=limit)
    
    async def get_trending(self, limit: int = 10) -> List[Prompt]:
        """Get trending prompts (sorted by recent views and likes)"""
        # This is a simplified trending algorithm
        # In production, you might want to use a more sophisticated algorithm
        return await self.get_by_filter({
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }, limit=limit, sort=[("views_count", -1), ("likes_count", -1)])
    
    async def get_recent(self, limit: int = 10) -> List[Prompt]:
        """Get recent prompts"""
        return await self.get_by_filter({
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }, limit=limit, sort=[("created_at", -1)])
    
    async def get_popular(self, limit: int = 10) -> List[Prompt]:
        """Get popular prompts (sorted by likes and views)"""
        return await self.get_by_filter({
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }, limit=limit, sort=[("likes_count", -1), ("views_count", -1)])
    
    async def search(self, query: str, limit: int = 20) -> List[Prompt]:
        """Search prompts by text"""
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}},
                {"content": {"$regex": query, "$options": "i"}}
            ],
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }
        
        return await self.repository.find_many(search_filter, limit=limit)
    
    async def get_by_filter(
        self, 
        filters: Dict[str, Any], 
        limit: int = 20,
        sort: Optional[List[tuple]] = None
    ) -> List[Prompt]:
        """Get prompts by custom filter"""
        return await self.repository.find_many(filters)
    
    async def increment_view(self, prompt_id: str) -> None:
        """Increment prompt view count"""
        prompt = await self.get_by_id(prompt_id)
        if prompt:
            prompt.increment_views()
            await prompt.save()
    
    async def increment_like(self, prompt_id: str) -> None:
        """Increment prompt like count"""
        prompt = await self.get_by_id(prompt_id)
        if prompt:
            prompt.increment_likes()
            await prompt.save()
    
    async def decrement_like(self, prompt_id: str) -> None:
        """Decrement prompt like count"""
        prompt = await self.get_by_id(prompt_id)
        if prompt:
            prompt.decrement_likes()
            await prompt.save()
    
    async def publish(self, prompt_id: str) -> Optional[Prompt]:
        """Publish a prompt"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        prompt.publish()
        await prompt.save()
        return prompt
    
    async def archive(self, prompt_id: str) -> Optional[Prompt]:
        """Archive a prompt"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        prompt.archive()
        await prompt.save()
        return prompt
    
    async def get_related_prompts(self, prompt: Prompt, limit: int = 5) -> List[Prompt]:
        """Get related prompts based on category and tags"""
        # Find prompts with same category or similar tags
        related_filter = {
            "$or": [
                {"category_id": prompt.category_id},
                {"tags": {"$in": prompt.tags}}
            ],
            "_id": {"$ne": prompt.id},
            "status": PromptStatus.PUBLISHED,
            "is_active": True
        }
        
        return await self.repository.find_many(related_filter)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get prompt statistics"""
        total_prompts = await self.repository.count()
        published_prompts = await self.repository.count({"status": PromptStatus.PUBLISHED})
        draft_prompts = await self.repository.count({"status": PromptStatus.DRAFT})
        featured_prompts = await self.repository.count({"is_featured": True})
        premium_prompts = await self.repository.count({"is_premium": True})
        
        # Calculate total views and likes
        all_prompts = await self.repository.find_many({})
        total_views = sum(prompt.views_count for prompt in all_prompts)
        total_likes = sum(prompt.likes_count for prompt in all_prompts)
        
        # Calculate average rating
        rated_prompts = [p for p in all_prompts if p.rating_count > 0]
        average_rating = sum(p.rating for p in rated_prompts) / len(rated_prompts) if rated_prompts else 0
        
        return {
            "total_prompts": total_prompts,
            "published_prompts": published_prompts,
            "draft_prompts": draft_prompts,
            "featured_prompts": featured_prompts,
            "premium_prompts": premium_prompts,
            "total_views": total_views,
            "total_likes": total_likes,
            "average_rating": round(average_rating, 2)
        }
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        import re
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug
    
    async def validate_create(self, prompt_in: PromptCreate) -> None:
        """Validate prompt creation"""
        # Check if title is unique (optional validation)
        existing_prompt = await self.repository.find_one({"title": prompt_in.title})
        if existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt with this title already exists"
            )
    
    async def validate_update(self, prompt_id: str, prompt_in: PromptUpdate) -> None:
        """Validate prompt update"""
        # Check if title is unique (if being updated)
        if prompt_in.title:
            existing_prompt = await self.repository.find_one({"title": prompt_in.title})
            if existing_prompt and str(existing_prompt.id) != prompt_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Prompt with this title already exists"
                )
