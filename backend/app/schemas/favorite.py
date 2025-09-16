from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.schemas.prompt import PromptSummary


# Request schemas
class FavoriteCreate(BaseModel):
    """Favorite creation schema"""
    prompt_id: str


# Response schemas
class FavoriteResponse(BaseModel):
    """Favorite response schema"""
    id: str
    user_id: str
    prompt_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteWithPrompt(BaseModel):
    """Favorite with prompt details"""
    id: str
    prompt: PromptSummary
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteStatus(BaseModel):
    """Favorite status schema"""
    is_favorite: bool
    favorites_count: int


class UserFavorites(BaseModel):
    """User favorites list schema"""
    user_id: str
    favorites: List[FavoriteWithPrompt]
    total_count: int
