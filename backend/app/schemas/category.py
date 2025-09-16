from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# Base schemas  
class CategoryBase(BaseModel):
    """Base category schema - simplified"""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


# Request schemas
class CategoryCreate(CategoryBase):
    """Category creation schema"""
    order: int = 0


class CategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


# Response schemas
class CategoryResponse(CategoryBase):
    """Category response schema"""
    id: str
    order: int
    is_active: bool
    prompts_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    """Category summary schema for lists"""
    id: str
    name: str
    icon: Optional[str] = None
    prompts_count: int
    
    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """Category statistics schema"""
    total_categories: int
    active_categories: int


# Admin schemas
class CategoryAdmin(CategoryResponse):
    """Admin category schema"""
    created_by: Optional[str] = None
