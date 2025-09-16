from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

from app.core.security import security_manager


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


class Admin(Document):
    """Admin user model"""
    
    email: EmailStr = Indexed(unique=True)
    username: str = Indexed(unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: AdminRole = AdminRole.ADMIN
    
    # Status
    is_active: bool = True
    is_verified: bool = True
    
    # Password reset
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    
    # Activity tracking
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "admins"
        indexes = [
            "email",
            "username",
            "is_active",
            "role"
        ]
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return security_manager.verify_password(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.hashed_password = security_manager.get_password_hash(password)
    
    def update_login(self) -> None:
        """Update login statistics"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.updated_at = datetime.utcnow()
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == AdminRole.SUPER_ADMIN
    
    def can_manage_admins(self) -> bool:
        """Check if user can manage other admins"""
        return self.role == AdminRole.SUPER_ADMIN



