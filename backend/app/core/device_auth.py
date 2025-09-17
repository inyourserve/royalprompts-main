from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.security import security_manager
from app.models.device import DeviceUser
from app.services.device_service import DeviceService

# Device-based security scheme
device_security = HTTPBearer(auto_error=False)


async def get_device_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(device_security)
) -> DeviceUser:
    """
    Get device user from token or create anonymous user
    Supports complete anonymous browsing without any registration
    """
    device_service = DeviceService()
    
    # If token provided, try to authenticate existing anonymous session
    if credentials:
        try:
            user_id = security_manager.verify_token(credentials.credentials)
            if user_id:
                device_user = await device_service.get_by_id(user_id)
                if device_user:
                    device_user.update_activity()
                    await device_user.save()
                    return device_user
        except:
            pass  # Fall through to create new anonymous user
    
    # Create anonymous user session
    device_id = request.headers.get("x-device-id")
    if not device_id:
        # Generate anonymous device ID if not provided
        import uuid
        device_id = f"anon_{str(uuid.uuid4())[:12]}"
    
    # Get device info from headers (optional for anonymous users)
    device_info = {
        "device_type": request.headers.get("x-device-type", "android"),  # Default to android instead of mobile
        "device_model": request.headers.get("x-device-model", "anonymous"),
        "os_version": request.headers.get("x-os-version", "unknown"),
        "app_version": request.headers.get("x-app-version", "1.0.0"),
        "user_type": "anonymous"
    }
    
    # Get or create anonymous device user  
    device_user = await device_service.get_or_create_device_user(
        device_id, device_info, request
    )
    
    return device_user


async def get_active_device_user(
    device_user: DeviceUser = Depends(get_device_user)
) -> DeviceUser:
    """Get active device user and check if blocked"""
    if device_user.is_blocked or not device_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device access has been blocked"
        )
    
    # Check rate limits
    device_service = DeviceService()
    await device_service.check_rate_limit(device_user)
    
    return device_user


async def get_authenticated_device_user(
    credentials: HTTPAuthorizationCredentials = Depends(device_security)
) -> DeviceUser:
    """Get authenticated device user - requires valid token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid token."
        )
    
    try:
        user_id = security_manager.verify_token(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        device_service = DeviceService()
        device_user = await device_service.get_by_id(user_id)
        if not device_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Device user not found"
            )
        
        if device_user.is_blocked or not device_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device access has been blocked"
            )
        
        # Update activity and check rate limits
        device_user.update_activity()
        await device_user.save()
        await device_service.check_rate_limit(device_user)
        
        return device_user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_premium_device_user(
    device_user: DeviceUser = Depends(get_active_device_user)
) -> DeviceUser:
    """Get premium device user"""
    if not device_user.can_access_premium_content():
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "Premium content requires subscription",
                "message": "This content is only available for premium users.",
                "upgrade_available": True,
                "user_type": device_user.user_type
            }
        )
    return device_user


def create_device_token(device_user: DeviceUser) -> str:
    """Create JWT token for device user"""
    expires_delta = timedelta(days=30)  # Long-lived for mobile apps
    return security_manager.create_access_token(
        subject=str(device_user.id),
        expires_delta=expires_delta
    )
