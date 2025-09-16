"""
Social Link Model
Handles social media links and channels
"""
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import HttpUrl


class SocialLink(Document):
    """Social media link model"""
    
    platform: Indexed(str, unique=True)  # Twitter, Facebook, Instagram, etc.
    url: HttpUrl
    is_active: bool = True
    display_order: int = 0  # For ordering in UI
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "social_links"
        use_enum_values = True
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_default_links(cls) -> list["SocialLink"]:
        """Get default social links"""
        return [
            cls(
                platform="Twitter",
                url="https://twitter.com/royalprompts",
                is_active=True,
                display_order=1
            ),
            cls(
                platform="Facebook", 
                url="https://facebook.com/royalprompts",
                is_active=True,
                display_order=2
            ),
            cls(
                platform="Instagram",
                url="https://instagram.com/royalprompts", 
                is_active=True,
                display_order=3
            ),
            cls(
                platform="LinkedIn",
                url="https://linkedin.com/company/royalprompts",
                is_active=False,
                display_order=4
            ),
            cls(
                platform="YouTube",
                url="https://youtube.com/@royalprompts",
                is_active=False,
                display_order=5
            ),
            cls(
                platform="Discord",
                url="https://discord.gg/royalprompts",
                is_active=True,
                display_order=6
            )
        ]
