from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class Category(Document):
    """Category document model - simplified for admin panel and mobile app"""
    
    # Essential fields only
    name: str = Indexed(unique=True)
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    order: int = 0
    prompts_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "categories"
        indexes = [
            "name",
            "is_active",
            "order"
        ]
    
    def increment_prompts_count(self) -> None:
        """Increment prompts count"""
        self.prompts_count += 1
    
    def decrement_prompts_count(self) -> None:
        """Decrement prompts count"""
        if self.prompts_count > 0:
            self.prompts_count -= 1
