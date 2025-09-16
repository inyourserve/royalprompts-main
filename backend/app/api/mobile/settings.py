"""
Mobile Settings API Endpoints
Public settings endpoints for mobile app
"""
from fastapi import APIRouter

from app.schemas.settings import AppSettingsPublic
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/app", response_model=AppSettingsPublic, tags=["Mobile Settings"])
async def get_public_app_settings():
    """Get public app settings for mobile app"""
    settings_service = SettingsService()
    settings = await settings_service.get_app_settings()
    
    # Return only public fields
    return AppSettingsPublic.model_validate(settings.model_dump())