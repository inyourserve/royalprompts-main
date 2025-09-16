"""
Admin Device Users API Endpoints
Handles device user management for admin panel
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime, timedelta

from app.core.admin_auth import get_current_admin
from app.schemas.device_admin import (
    DeviceUserAdmin, 
    DeviceUserUpdate,
    DeviceUserListResponse,
    DeviceUserStats
)
from app.services.device_service import DeviceService
from app.models.device import DeviceUser, DeviceType

router = APIRouter()


@router.get("/", response_model=DeviceUserListResponse, tags=["Admin Users"])
async def get_device_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: Optional[str] = Query(None),
    device_type: Optional[DeviceType] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_blocked: Optional[bool] = Query(None),
    current_admin = Depends(get_current_admin)
):
    """Get device users for admin management"""
    device_service = DeviceService()
    
    # Build filters
    filters = {}
    if device_type is not None:
        filters["device_type"] = device_type
    if is_active is not None:
        filters["is_active"] = is_active
    if is_blocked is not None:
        filters["is_blocked"] = is_blocked
    
    # Get users with pagination
    skip = (page - 1) * limit
    
    if search:
        # Simple search by device_id
        users = await DeviceUser.find(
            DeviceUser.device_id.contains(search)
        ).skip(skip).limit(limit).to_list()
        total = await DeviceUser.find(
            DeviceUser.device_id.contains(search)
        ).count()
    else:
        # Apply filters
        query = DeviceUser.find()
        for key, value in filters.items():
            query = query.find(getattr(DeviceUser, key) == value)
        
        users = await query.skip(skip).limit(limit).to_list()
        total = await query.count()
    
    # Convert to admin format
    admin_users = []
    for user in users:
        user_dict = user.model_dump()
        user_dict["id"] = str(user.id)
        
        # Calculate total favorites from favorites collection
        from app.services.favorite_service import FavoriteService
        favorite_service = FavoriteService()
        total_favorites = await favorite_service.get_device_favorites_count(user.device_id)
        user_dict["total_favorites"] = total_favorites
        admin_users.append(DeviceUserAdmin.model_validate(user_dict))
    
    return DeviceUserListResponse(
        items=admin_users,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/stats", response_model=DeviceUserStats, tags=["Admin Users"])
async def get_device_user_stats(current_admin = Depends(get_current_admin)):
    """Get device user statistics"""
    # Total users
    total_users = await DeviceUser.count()
    active_users = await DeviceUser.find(DeviceUser.is_active == True).count()
    blocked_users = await DeviceUser.find(DeviceUser.is_blocked == True).count()
    
    # Device type breakdown
    android_users = await DeviceUser.find(DeviceUser.device_type == DeviceType.ANDROID).count()
    ios_users = await DeviceUser.find(DeviceUser.device_type == DeviceType.IOS).count()
    web_users = await DeviceUser.find(DeviceUser.device_type == DeviceType.WEB).count()
    
    # New users
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    new_users_today = await DeviceUser.find(DeviceUser.first_seen >= today).count()
    new_users_this_week = await DeviceUser.find(DeviceUser.first_seen >= week_ago).count()
    new_users_this_month = await DeviceUser.find(DeviceUser.first_seen >= month_ago).count()
    
    # Most active country
    pipeline = [
        {"$match": {"country": {"$ne": None}}},
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    country_result = await DeviceUser.aggregate(pipeline).to_list(1)
    most_active_country = country_result[0]["_id"] if country_result else None
    
    # Total requests
    total_requests_today = sum([user.daily_requests for user in await DeviceUser.find().to_list()])
    
    # This week requests (simplified - in production you'd want more sophisticated tracking)
    total_requests_this_week = total_requests_today * 7  # Rough estimate
    
    return DeviceUserStats(
        total_users=total_users,
        active_users=active_users,
        blocked_users=blocked_users,
        android_users=android_users,
        ios_users=ios_users,
        web_users=web_users,
        new_users_today=new_users_today,
        new_users_this_week=new_users_this_week,
        new_users_this_month=new_users_this_month,
        most_active_country=most_active_country,
        total_requests_today=total_requests_today,
        total_requests_this_week=total_requests_this_week
    )


@router.get("/{user_id}", response_model=DeviceUserAdmin, tags=["Admin Users"])
async def get_device_user(
    user_id: str,
    current_admin = Depends(get_current_admin)
):
    """Get a specific device user"""
    device_service = DeviceService()
    user = await device_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device user not found"
        )
    
    user_dict = user.model_dump()
    user_dict["id"] = str(user.id)
    user_dict["total_favorites"] = len(user.favorite_prompts)
    
    return DeviceUserAdmin.model_validate(user_dict)


@router.put("/{user_id}", response_model=DeviceUserAdmin, tags=["Admin Users"])
async def update_device_user(
    user_id: str,
    user_data: DeviceUserUpdate,
    current_admin = Depends(get_current_admin)
):
    """Update a device user"""
    device_service = DeviceService()
    
    try:
        updated_user = await device_service.update(user_id, user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device user not found"
            )
        
        user_dict = updated_user.model_dump()
        user_dict["id"] = str(updated_user.id)
        user_dict["total_favorites"] = len(updated_user.favorite_prompts)
        
        return DeviceUserAdmin.model_validate(user_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device user: {str(e)}"
        )


@router.delete("/{user_id}", tags=["Admin Users"])
async def delete_device_user(
    user_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete a device user"""
    device_service = DeviceService()
    
    try:
        success = await device_service.delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device user not found"
            )
        
        return {"message": "Device user deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device user: {str(e)}"
        )


@router.post("/{user_id}/block", response_model=DeviceUserAdmin, tags=["Admin Users"])
async def block_device_user(
    user_id: str,
    current_admin = Depends(get_current_admin)
):
    """Block a device user"""
    device_service = DeviceService()
    
    try:
        user = await device_service.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device user not found"
            )
        
        user.is_blocked = True
        user.is_active = False
        await user.save()
        
        user_dict = user.model_dump()
        user_dict["id"] = str(user.id)
        user_dict["total_favorites"] = len(user.favorite_prompts)
        
        return DeviceUserAdmin.model_validate(user_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block device user: {str(e)}"
        )


@router.post("/{user_id}/unblock", response_model=DeviceUserAdmin, tags=["Admin Users"])
async def unblock_device_user(
    user_id: str,
    current_admin = Depends(get_current_admin)
):
    """Unblock a device user"""
    device_service = DeviceService()
    
    try:
        user = await device_service.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device user not found"
            )
        
        user.is_blocked = False
        user.is_active = True
        await user.save()
        
        user_dict = user.model_dump()
        user_dict["id"] = str(user.id)
        user_dict["total_favorites"] = len(user.favorite_prompts)
        
        return DeviceUserAdmin.model_validate(user_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock device user: {str(e)}"
        )
