from typing import Optional
from fastapi import HTTPException, status, Request
from datetime import datetime, timedelta
import uuid

from app.services.base import BaseService
from app.models.device import DeviceUser, DeviceType, UserType
from app.db.base import MongoRepository


class DeviceService(BaseService[DeviceUser, dict, dict]):
    """Device-based user management service"""
    
    def __init__(self):
        repository = MongoRepository(DeviceUser)
        super().__init__(repository)
    
    async def get_or_create_device_user(
        self, 
        device_id: str,
        device_info: dict,
        request: Request
    ) -> DeviceUser:
        """Get existing device user or create new anonymous user"""
        
        # Try to find existing device user
        device_user = await self.repository.find_one({"device_id": device_id})
        
        if device_user:
            # Update activity and return existing user
            device_user.update_activity()
            
            # Update device info if provided
            if device_info.get("device_type"):
                device_user.device_type = device_info["device_type"]
            if device_info.get("device_model"):
                device_user.device_model = device_info["device_model"]
            if device_info.get("os_version"):
                device_user.os_version = device_info["os_version"]
            if device_info.get("app_version"):
                device_user.app_version = device_info["app_version"]
            
            # Update IP and user agent
            device_user.ip_address = request.client.host if request.client else None
            device_user.user_agent = request.headers.get("user-agent")
            
            await device_user.save()
            return device_user
        
        # Create new anonymous device user
        device_user = DeviceUser(
            device_id=device_id,
            device_type=device_info.get("device_type", DeviceType.ANDROID),
            device_model=device_info.get("device_model"),
            os_version=device_info.get("os_version"),
            app_version=device_info.get("app_version"),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_type=UserType.ANONYMOUS
        )
        
        device_user.update_activity()
        await device_user.create()
        
        return device_user
    
    async def check_rate_limit(self, device_user: DeviceUser) -> bool:
        """Check if device user is within rate limits"""
        # For now, no rate limiting since we removed premium features
        # You can add simple rate limiting here if needed
        return True
    
    
    async def add_to_favorites(self, device_user: DeviceUser, prompt_id: str) -> None:
        """Add prompt to device user favorites"""
        # Use the proper favorites service instead of arrays
        from app.services.favorite_service import FavoriteService
        favorite_service = FavoriteService()
        await favorite_service.add_favorite(device_user.device_id, prompt_id)
    
    async def remove_from_favorites(self, device_user: DeviceUser, prompt_id: str) -> None:
        """Remove prompt from device user favorites"""
        # Use the proper favorites service instead of arrays
        from app.services.favorite_service import FavoriteService
        favorite_service = FavoriteService()
        await favorite_service.remove_favorite(device_user.device_id, prompt_id)
    
    async def unlock_prompt(self, device_user: DeviceUser, prompt_id: str) -> None:
        """Unlock a prompt for this device"""
        device_user.unlock_prompt(prompt_id)
        await device_user.save()
    
    async def is_prompt_unlocked(self, device_user: DeviceUser, prompt_id: str) -> bool:
        """Check if a prompt is unlocked for this device"""
        return device_user.has_unlocked_prompt(prompt_id)
    
    async def get_user_stats(self) -> dict:
        """Get device user statistics"""
        total_devices = await self.repository.count()
        active_today = await self.repository.count({
            "last_seen": {"$gte": datetime.utcnow() - timedelta(days=1)}
        })
        
        return {
            "total_devices": total_devices,
            "active_today": active_today,
            "anonymous_users": total_devices
        }
    
    async def block_device(self, device_id: str) -> DeviceUser:
        """Block a device (admin function)"""
        device_user = await self.repository.find_one({"device_id": device_id})
        if not device_user:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_user.is_blocked = True
        device_user.is_active = False
        await device_user.save()
        return device_user
    
    async def validate_create(self, obj_in: dict) -> None:
        """Validate device user creation"""
        pass
    
    async def validate_update(self, device_id: str, obj_in: dict) -> None:
        """Validate device user update"""
        pass
