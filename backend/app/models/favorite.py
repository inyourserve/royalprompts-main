from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime


class Favorite(Document):
    """Favorite document model for device-prompt relationships"""
    
    device_id: str = Indexed()  # Changed from user_id to device_id for clarity
    prompt_id: str = Indexed()
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "favorites"
        indexes = [
            "device_id",
            "prompt_id",
            [("device_id", 1), ("prompt_id", 1)],  # Compound index
            "created_at"
        ]
