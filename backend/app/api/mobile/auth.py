"""
Mobile App Authentication Endpoints
Handles anonymous login and device sessions
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Body
from app.core.device_auth import get_active_device_user, create_device_token
from app.schemas.device import DeviceRegistration, ApiKeyResponse, RateLimitInfo
from app.services.device_service import DeviceService

router = APIRouter()


@router.post("/anonymous-login", response_model=ApiKeyResponse, tags=["Mobile Auth"])
async def anonymous_login(
    request: Request
):
    """
    Anonymous login - No registration required!
    Creates anonymous user session for immediate app usage
    """
    device_service = DeviceService()
    
    # Try to get device info from request body, but don't require it
    try:
        body = await request.json()
        device_info = body if body else {}
    except:
        device_info = {}
    
    # Generate anonymous device ID if not provided
    if not device_info.get("device_id"):
        import uuid
        device_id = f"anon_{str(uuid.uuid4())[:8]}"
        device_info["device_id"] = device_id
    
    # Set default values for required fields
    from app.models.device import DeviceType
    if not device_info.get("device_type"):
        device_info["device_type"] = DeviceType.ANDROID
    if not device_info.get("device_model"):
        device_info["device_model"] = "anonymous"
    if not device_info.get("os_version"):
        device_info["os_version"] = "unknown"
    if not device_info.get("app_version"):
        device_info["app_version"] = "1.0.0"
    
    # Create anonymous device user
    device_user = await device_service.get_or_create_device_user(
        device_info["device_id"],
        device_info,
        request
    )
    
    # Create anonymous session token
    device_token = create_device_token(device_user)
    rate_limits = RateLimitInfo(
        daily_limit=100,  # Generous limits for anonymous users
        daily_used=device_user.daily_requests,
        monthly_limit=1000,
        monthly_used=0,
        is_premium=False,
        can_upgrade=False
    )
    
    return ApiKeyResponse(
        device_token=device_token,
        expires_in=30 * 24 * 60 * 60,  # 30 days session
        device_id=device_user.device_id,
        user_type="anonymous",
        rate_limits=rate_limits
    )


# Only anonymous-login endpoint needed - removed redundant register and session endpoints
