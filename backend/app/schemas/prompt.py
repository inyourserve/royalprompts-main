from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.prompt import PromptStatus


# Base schemas
class PromptBase(BaseModel):
    """Base prompt schema - simplified"""
    title: str
    description: str
    content: str
    category_id: str


# Request schemas
class PromptCreate(PromptBase):
    """Prompt creation schema"""
    image_url: Optional[str] = None
    is_featured: bool = False


class PromptUpdate(BaseModel):
    """Prompt update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[str] = None
    status: Optional[PromptStatus] = None
    is_featured: Optional[bool] = None


class PromptFilter(BaseModel):
    """Prompt filtering schema"""
    category_id: Optional[str] = None
    status: Optional[PromptStatus] = None
    is_featured: Optional[bool] = None
    search: Optional[str] = None


class PromptSort(BaseModel):
    """Prompt sorting schema"""
    field: str = "created_at"
    order: str = "desc"  # asc or desc


# Response schemas
class PromptResponse(PromptBase):
    """Prompt response schema"""
    id: str
    image_url: Optional[str] = None
    status: PromptStatus
    is_featured: bool
    is_active: bool
    likes_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PromptSummary(BaseModel):
    """Prompt summary schema for lists"""
    id: str
    title: str
    description: str

    image_url: Optional[str] = None
    category_id: str
    is_featured: bool
    likes_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PromptDetail(PromptResponse):
    """Detailed prompt schema"""
    category_name: Optional[str] = None
    is_favorited: bool = False
    related_prompts: List[PromptSummary] = []


class PromptStats(BaseModel):
    """Prompt statistics schema"""
    total_prompts: int
    published_prompts: int
    draft_prompts: int
    featured_prompts: int
    premium_prompts: int
    total_views: int
    total_likes: int
    average_rating: float


# Admin schemas
class PromptAdmin(PromptResponse):
    """Admin prompt schema with additional fields"""
    created_by: Optional[str] = None
