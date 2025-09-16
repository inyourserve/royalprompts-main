from pydantic import BaseModel
from typing import List, Optional, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


# Pagination schemas
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    size: int = 20
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(
        cls, 
        items: List[T], 
        total: int, 
        pagination: PaginationParams
    ) -> "PaginatedResponse[T]":
        """Create paginated response"""
        pages = (total + pagination.size - 1) // pagination.size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )


# Response wrappers
class SuccessResponse(BaseModel):
    """Success response schema"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    details: Optional[Any] = None


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str
    database: str


# File upload schemas
class FileUploadResponse(BaseModel):
    """File upload response schema"""
    filename: str
    url: str
    size: int
    content_type: str


class ImageUploadResponse(FileUploadResponse):
    """Image upload response schema"""
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


# Search schemas
class SearchParams(BaseModel):
    """Search parameters"""
    query: str
    filters: Optional[dict] = None
    sort: Optional[str] = None
    page: int = 1
    size: int = 20


class SearchResponse(BaseModel, Generic[T]):
    """Search response schema"""
    query: str
    results: List[T]
    total: int
    took: float  # Search time in seconds
    suggestions: List[str] = []


# Statistics schemas
class AppStats(BaseModel):
    """Application statistics schema"""
    total_users: int
    total_prompts: int
    total_categories: int
    total_favorites: int
    active_users: int
    featured_prompts: int
    premium_users: int
    
    # Daily stats
    daily_new_users: int
    daily_new_prompts: int
    daily_views: int
    daily_likes: int


class DashboardStats(BaseModel):
    """Dashboard statistics schema"""
    today_stats: dict
    week_stats: dict
    month_stats: dict
    popular_prompts: List[dict]
    popular_categories: List[dict]
    recent_activity: List[dict]
