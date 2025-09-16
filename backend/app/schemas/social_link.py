"""
Social Link Schemas
Pydantic schemas for social media links
"""
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


class SocialLinkBase(BaseModel):
    """Base social link schema"""
    platform: str = Field(..., min_length=1, max_length=50)
    url: HttpUrl
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)


class SocialLinkCreate(SocialLinkBase):
    """Schema for creating social links"""
    pass


class SocialLinkUpdate(BaseModel):
    """Schema for updating social links"""
    platform: Optional[str] = Field(None, min_length=1, max_length=50)
    url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class SocialLinkResponse(SocialLinkBase):
    """Schema for social link responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SocialLinksListResponse(BaseModel):
    """Schema for social links list response"""
    items: List[SocialLinkResponse]
    total: int


class SocialLinkPublic(BaseModel):
    """Public schema for social links (no sensitive data)"""
    platform: str
    url: str
    is_active: bool
    display_order: int
    
    class Config:
        from_attributes = True


class SocialLinksPublicListResponse(BaseModel):
    """Schema for public social links list response"""
    items: List[SocialLinkPublic]
    total: int


class SocialLinksBulkUpdate(BaseModel):
    """Schema for bulk updating social links"""
    links: List[SocialLinkUpdate] = Field(..., min_items=1)
