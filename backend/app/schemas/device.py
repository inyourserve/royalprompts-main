from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.device import DeviceType, UserType


# Request schemas
class DeviceRegistration(BaseModel):
    """Device registration/identification schema"""
    device_id: str
    device_type: DeviceType
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Device update schema"""
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    preferences: Optional[dict] = None


class PremiumUpgrade(BaseModel):
    """Premium upgrade schema"""
    subscription_id: str
    duration_days: int = 30


# Response schemas
class DeviceUserResponse(BaseModel):
    """Device user response schema"""
    device_id: str
    device_type: DeviceType
    user_type: UserType
    is_active: bool
    
    # Usage info
    total_requests: int
    daily_requests: int
    
    # Activity
    first_seen: datetime
    last_seen: datetime
    
    model_config = {"from_attributes": True}


class DeviceUserProfile(DeviceUserResponse):
    """Extended device user profile"""
    # Note: Favorites are handled by separate 'favorites' collection
    favorite_categories: List[str] = []
    preferences: Dict[str, Any] = {}


class DeviceStats(BaseModel):
    """Device statistics schema"""
    total_devices: int
    active_today: int
    premium_users: int
    anonymous_users: int


class RateLimitInfo(BaseModel):
    """Rate limit information schema"""
    daily_limit: int
    daily_used: int
    monthly_limit: int
    monthly_used: int
    is_premium: bool
    can_upgrade: bool
    reset_time: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    """API key response for device authentication"""
    device_token: str
    expires_in: int
    device_id: str
    user_type: UserType
    rate_limits: RateLimitInfo
