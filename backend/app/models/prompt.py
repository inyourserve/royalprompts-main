from beanie import Document, Indexed
from pydantic import Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PromptStatus(str, Enum):
    """Simplified prompt status"""
    DRAFT = "draft"
    PUBLISHED = "published"


class Prompt(Document):
    """Prompt document model - simplified for admin panel and mobile app"""
    
    # Essential fields only
    title: str = Indexed()
    description: str
    content: str  # The actual prompt text
    category_id: str = Indexed()
    
    # Basic flags
    status: PromptStatus = PromptStatus.PUBLISHED
    is_featured: bool = False
    is_active: bool = True
    
    # Media
    image_url: Optional[str] = None
    
    # Simple metrics for mobile app
    likes_count: int = 0
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "prompts"
        indexes = [
            "title",
            "category_id", 
            "status",
            "is_featured",
            "is_active",
            "created_at"
        ]
    
    def increment_likes(self) -> None:
        """Increment like count"""
        self.likes_count += 1
    
    def decrement_likes(self) -> None:
        """Decrement like count"""
        if self.likes_count > 0:
            self.likes_count -= 1
    
    def increment_views(self) -> None:
        """Increment view count (placeholder - views not tracked in simplified model)"""
        # Views are not tracked in the simplified model
        # This method exists to prevent errors when called from PromptService
        pass