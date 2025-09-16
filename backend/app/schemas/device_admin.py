"""
Device User Admin Schemas
Pydantic schemas for device user management in admin panel
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.device import DeviceType, UserType


class DeviceUserAdmin(BaseModel):
    """Admin schema for device user management"""
    id: str
    device_id: str
    device_type: DeviceType
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    
    # User classification
    user_type: UserType
    is_active: bool
    is_blocked: bool
    
    # Usage tracking
    first_seen: datetime
    last_seen: datetime
    total_requests: int
    daily_requests: int
    
    # Location and metadata
    country: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Favorites and usage (calculated from separate collections)
    total_favorites: int = 0
    
    class Config:
        from_attributes = True


class DeviceUserUpdate(BaseModel):
    """Schema for updating device user"""
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None


class DeviceUserListResponse(BaseModel):
    """Schema for device user list response"""
    items: List[DeviceUserAdmin]
    total: int
    page: int
    limit: int


class DeviceUserStats(BaseModel):
    """Schema for device user statistics"""
    total_users: int
    active_users: int
    blocked_users: int
    android_users: int
    ios_users: int
    web_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    most_active_country: Optional[str] = None
    total_requests_today: int
    total_requests_this_week: int
