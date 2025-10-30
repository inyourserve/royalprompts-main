from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime


class Unlock(Document):
    """Unlock document model for tracking when devices unlock prompts (for ad revenue tracking)"""
    
    device_id: str = Indexed()
    prompt_id: str = Indexed()
    
    # Metadata
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "unlocks"
        indexes = [
            "device_id",
            "prompt_id",
            "unlocked_at"
        ]
        # Note: No unique compound index - users can unlock the same prompt multiple times
        # Each unlock = one ad view = more revenue

