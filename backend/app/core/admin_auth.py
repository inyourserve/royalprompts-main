from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import security_manager
from app.models.admin import Admin, AdminRole
from app.services.admin_service import AdminService

# Admin security scheme
admin_security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(admin_security)
) -> Admin:
    """Get current authenticated admin"""
    try:
        admin_id = security_manager.verify_token(credentials.credentials)
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        admin_service = AdminService()
        admin = await admin_service.get_by_id(admin_id)
        if not admin or not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found or inactive"
            )
        
        return admin
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_super_admin(
    admin: Admin = Depends(get_current_admin)
) -> Admin:
    """Get current authenticated super admin"""
    if not admin.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return admin


def create_admin_token(admin: Admin) -> str:
    """Create JWT token for admin"""
    return security_manager.create_access_token(subject=str(admin.id))



