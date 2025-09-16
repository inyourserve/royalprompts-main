"""
Settings Service
Business logic for application settings management
"""
from typing import Optional
from app.services.base import BaseService
from app.models.settings import AppSettings
from app.db.base import MongoRepository


class SettingsService(BaseService[AppSettings, dict, dict]):
    """Settings management service"""
    
    def __init__(self):
        repository = MongoRepository(AppSettings)
        super().__init__(repository)
    
    async def get_app_settings(self) -> AppSettings:
        """Get current app settings or create default ones"""
        settings = await AppSettings.find_one()
        if not settings:
            # Create default settings
            settings = AppSettings.get_default_settings()
            await settings.create()
        return settings
    
    async def update_app_settings(self, settings_data: dict) -> AppSettings:
        """Update app settings"""
        current_settings = await self.get_app_settings()
        
        # Update only provided fields
        for field, value in settings_data.items():
            if hasattr(current_settings, field) and value is not None:
                setattr(current_settings, field, value)
        
        current_settings.update_timestamp()
        await current_settings.save()
        return current_settings
    
    async def reset_to_default(self) -> AppSettings:
        """Reset settings to default values"""
        current_settings = await self.get_app_settings()
        
        # Reset to default values
        current_settings.app_name = "RoyalPrompts"
        current_settings.description = "Your AI prompt management platform"
        current_settings.about_text = "RoyalPrompts is a comprehensive platform for managing and organizing AI prompts. We help users discover, create, and share high-quality prompts for various AI models."
        current_settings.how_to_use = "1. Browse prompts by category\n2. Copy and use prompts with your AI\n3. Create and share your own prompts\n4. Save favorites for quick access"
        current_settings.contact_email = "support@royalprompts.com"
        
        current_settings.update_timestamp()
        await current_settings.save()
        return current_settings
    
    async def validate_create(self, obj_in: dict) -> None:
        """Validate settings creation"""
        pass
    
    async def validate_update(self, settings_id: str, obj_in: dict) -> None:
        """Validate settings update"""
        pass
