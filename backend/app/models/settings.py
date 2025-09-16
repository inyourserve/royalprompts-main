"""
Settings Model
Handles application configuration and settings
"""
from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import EmailStr


class AppSettings(Document):
    """Application settings model"""
    
    app_name: str = "RoyalPrompts"
    description: str = "Your AI prompt management platform"
    about_text: Optional[str] = None
    how_to_use: Optional[str] = None
    contact_email: EmailStr = "support@royalprompts.com"
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "app_settings"
        use_enum_values = True
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_default_settings(cls) -> "AppSettings":
        """Get default app settings instance"""
        return cls(
            app_name="RoyalPrompts",
            description="Your AI prompt management platform",
            about_text="RoyalPrompts is a comprehensive platform for managing and organizing AI prompts. We help users discover, create, and share high-quality prompts for various AI models.",
            how_to_use="1. Browse prompts by category\n2. Copy and use prompts with your AI\n3. Create and share your own prompts\n4. Save favorites for quick access",
            contact_email="support@royalprompts.com"
        )
