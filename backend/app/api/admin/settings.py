"""
Admin Settings API Endpoints
Handles application settings management for admin panel
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import get_current_admin
from app.schemas.settings import (
    AppSettingsResponse, 
    AppSettingsUpdate,
    AppSettingsCreate
)
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/app", response_model=AppSettingsResponse, tags=["Admin Settings"])
async def get_app_settings(current_admin = Depends(get_current_admin)):
    """Get current app settings"""
    settings_service = SettingsService()
    settings = await settings_service.get_app_settings()
    
    # Convert to response format
    settings_dict = settings.model_dump()
    settings_dict["id"] = str(settings.id)
    return AppSettingsResponse.model_validate(settings_dict)


@router.put("/app", response_model=AppSettingsResponse, tags=["Admin Settings"])
async def update_app_settings(
    settings_data: AppSettingsUpdate,
    current_admin = Depends(get_current_admin)
):
    """Update app settings"""
    settings_service = SettingsService()
    
    # Convert to dict and remove None values
    update_data = settings_data.model_dump(exclude_unset=True)
    
    try:
        updated_settings = await settings_service.update_app_settings(update_data)
        
        # Convert to response format
        settings_dict = updated_settings.model_dump()
        settings_dict["id"] = str(updated_settings.id)
        return AppSettingsResponse.model_validate(settings_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.post("/app", response_model=AppSettingsResponse, tags=["Admin Settings"])
async def create_app_settings(
    settings_data: AppSettingsCreate,
    current_admin = Depends(get_current_admin)
):
    """Create new app settings (replaces existing)"""
    settings_service = SettingsService()
    
    try:
        # This will update existing settings or create new ones
        create_data = settings_data.model_dump()
        updated_settings = await settings_service.update_app_settings(create_data)
        
        # Convert to response format
        settings_dict = updated_settings.model_dump()
        settings_dict["id"] = str(updated_settings.id)
        return AppSettingsResponse.model_validate(settings_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create settings: {str(e)}"
        )


@router.post("/app/reset", response_model=AppSettingsResponse, tags=["Admin Settings"])
async def reset_app_settings(current_admin = Depends(get_current_admin)):
    """Reset app settings to default values"""
    settings_service = SettingsService()
    
    try:
        reset_settings = await settings_service.reset_to_default()
        
        # Convert to response format
        settings_dict = reset_settings.model_dump()
        settings_dict["id"] = str(reset_settings.id)
        return AppSettingsResponse.model_validate(settings_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}"
        )
