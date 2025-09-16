from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from app.services.base import BaseService
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.db.base import MongoRepository


class CategoryService(BaseService[Category, CategoryCreate, CategoryUpdate]):
    """Category service for business logic"""
    
    def __init__(self):
        repository = MongoRepository(Category)
        super().__init__(repository)
    
    async def create_category(self, category_in: CategoryCreate) -> Category:
        """Create a new category"""
        await self.validate_create(category_in)
        
        category_data = category_in.dict()
        
        return await self.repository.create(category_data)
    
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        return await self.repository.find_one({"name": name})
    
    async def get_active_categories(self) -> List[Category]:
        """Get all active categories"""
        return await self.repository.find_many({"is_active": True})
    
    async def get_all(self) -> List[Category]:
        """Get all categories"""
        return await self.repository.find_many({})
    
    async def get_featured_categories(self) -> List[Category]:
        """Get featured categories"""
        return await self.repository.find_many({
            "is_active": True
        })
    
    async def get_categories_with_prompts(self) -> List[Category]:
        """Get categories that have prompts"""
        return await self.repository.find_many({
            "prompts_count": {"$gt": 0},
            "is_active": True
        })
    
    async def increment_prompts_count(self, category_id: str) -> None:
        """Increment prompts count for category"""
        category = await self.get_by_id(category_id)
        if category:
            category.increment_prompts_count()
            await category.save()
    
    async def decrement_prompts_count(self, category_id: str) -> None:
        """Decrement prompts count for category"""
        category = await self.get_by_id(category_id)
        if category:
            category.decrement_prompts_count()
            await category.save()
    
    async def update_prompts_count(self, category_id: str) -> None:
        """Update prompts count for category (recalculate from database)"""
        from app.services.prompt_service import PromptService
        
        prompt_service = PromptService()
        prompts = await prompt_service.get_by_category(category_id)
        
        category = await self.get_by_id(category_id)
        if category:
            category.prompts_count = len(prompts)
            await category.save()
    
    async def reorder_categories(self, category_orders: List[Dict[str, int]]) -> None:
        """Reorder categories"""
        for item in category_orders:
            category_id = item.get("id")
            order = item.get("order")
            
            if category_id and order is not None:
                await self.repository.update(category_id, {"order": order})
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get category statistics"""
        total_categories = await self.repository.count()
        active_categories = await self.repository.count({"is_active": True})
        featured_categories = 0  # Featured categories not implemented in current model
        categories_with_prompts = await self.repository.count({"prompts_count": {"$gt": 0}})
        
        # Calculate average prompts per category
        all_categories = await self.repository.find_many({})
        total_prompts = sum(cat.prompts_count for cat in all_categories)
        average_prompts = total_prompts / total_categories if total_categories > 0 else 0
        
        return {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "featured_categories": featured_categories,
            "categories_with_prompts": categories_with_prompts,
            "average_prompts_per_category": round(average_prompts, 2)
        }
    
    
    async def validate_create(self, category_in: CategoryCreate) -> None:
        """Validate category creation"""
        # Check if name exists
        existing_category = await self.get_by_name(category_in.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
    
    async def validate_update(self, category_id: str, category_in: CategoryUpdate) -> None:
        """Validate category update"""
        # Check if name exists (if being updated)
        if category_in.name:
            existing_category = await self.get_by_name(category_in.name)
            if existing_category and str(existing_category.id) != category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this name already exists"
                )
