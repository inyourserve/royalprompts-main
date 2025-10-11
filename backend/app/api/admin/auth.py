"""
Admin Panel Authentication Endpoints
Handles admin login and profile management
check 1 mb
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import get_current_admin, create_admin_token
from app.schemas.admin import AdminLogin, AdminLoginResponse, AdminResponse
from app.services.admin_service import AdminService

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse, tags=["Admin Auth"])
async def admin_login(login_data: AdminLogin):
    """Admin login for admin panel"""
    admin_service = AdminService()
    admin = await admin_service.authenticate(login_data.email, login_data.password)
    
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_admin_token(admin)
    admin_data = admin.model_dump()
    admin_data["id"] = str(admin.id)
    
    return AdminLoginResponse(
        access_token=access_token,
        expires_in=30 * 24 * 60 * 60,
        admin=AdminResponse.model_validate(admin_data)
    )


@router.get("/me", response_model=AdminResponse, tags=["Admin Auth"])
async def get_admin_profile(current_admin = Depends(get_current_admin)):
    """Get current admin profile"""
    admin_data = current_admin.model_dump()
    admin_data["id"] = str(current_admin.id)
    return AdminResponse.model_validate(admin_data)
