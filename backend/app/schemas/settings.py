"""
Settings Schemas
Pydantic schemas for settings validation and serialization
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AppSettingsBase(BaseModel):
    """Base app settings schema"""
    app_name: str
    description: str
    about_text: Optional[str] = None
    how_to_use: Optional[str] = None
    contact_email: EmailStr


class AppSettingsCreate(AppSettingsBase):
    """Create app settings schema"""
    pass


class AppSettingsUpdate(BaseModel):
    """Update app settings schema"""
    app_name: Optional[str] = None
    description: Optional[str] = None
    about_text: Optional[str] = None
    how_to_use: Optional[str] = None
    contact_email: Optional[EmailStr] = None


class AppSettingsResponse(AppSettingsBase):
    """App settings response schema"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class AppSettingsPublic(BaseModel):
    """Public app settings schema (for mobile app)"""
    app_name: str
    description: str
    about_text: Optional[str] = None
    how_to_use: Optional[str] = None
    contact_email: EmailStr
    
    model_config = {"from_attributes": True}
