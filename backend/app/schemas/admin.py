from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.admin import AdminRole


# Request schemas
class AdminLogin(BaseModel):
    """Admin login schema"""
    email: EmailStr
    password: str


class AdminCreate(BaseModel):
    """Admin creation schema"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: AdminRole = AdminRole.ADMIN


class AdminUpdate(BaseModel):
    """Admin update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str


# Response schemas
class AdminResponse(BaseModel):
    """Admin response schema"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: AdminRole
    is_active: bool
    last_login: Optional[datetime] = None
    login_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AdminLoginResponse(BaseModel):
    """Admin login response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: AdminResponse


class DashboardStats(BaseModel):
    """Dashboard statistics schema"""
    total_prompts: int
    total_categories: int
    total_devices: int
    active_devices_today: int
    total_favorites: int
    total_unlocks: int
    prompts_by_category: dict
    recent_activity: list



