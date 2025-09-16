"""
Social Link Service
Business logic for social media links management
"""
from typing import List, Optional
from app.services.base import BaseService
from app.models.social_link import SocialLink
from app.db.base import MongoRepository
from app.schemas.social_link import SocialLinkCreate, SocialLinkUpdate


class SocialLinkService(BaseService[SocialLink, SocialLinkCreate, SocialLinkUpdate]):
    """Social links management service"""
    
    def __init__(self):
        repository = MongoRepository(SocialLink)
        super().__init__(repository)
    
    async def get_all_social_links(self) -> List[SocialLink]:
        """Get all social links ordered by display_order"""
        return await SocialLink.find().sort("display_order").to_list()
    
    async def get_active_social_links(self) -> List[SocialLink]:
        """Get only active social links ordered by display_order"""
        return await SocialLink.find(SocialLink.is_active == True).sort("display_order").to_list()
    
    async def get_social_link_by_platform(self, platform: str) -> Optional[SocialLink]:
        """Get social link by platform name"""
        return await SocialLink.find_one(SocialLink.platform == platform)
    
    async def create_or_update_social_link(self, platform: str, link_data: SocialLinkCreate) -> SocialLink:
        """Create new social link or update existing one by platform"""
        existing_link = await self.get_social_link_by_platform(platform)
        
        if existing_link:
            # Update existing link
            update_data = link_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_link, field, value)
            existing_link.update_timestamp()
            await existing_link.save()
            return existing_link
        else:
            # Create new link
            new_link = SocialLink(**link_data.model_dump())
            await new_link.create()
            return new_link
    
    async def bulk_update_social_links(self, links_data: List[SocialLinkUpdate]) -> List[SocialLink]:
        """Bulk update social links"""
        updated_links = []
        
        for i, link_data in enumerate(links_data):
            # Get existing link by index (assuming order matches frontend)
            existing_links = await self.get_all_social_links()
            if i < len(existing_links):
                existing_link = existing_links[i]
                
                # Update fields
                update_data = link_data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(existing_link, field, value)
                
                existing_link.update_timestamp()
                await existing_link.save()
                updated_links.append(existing_link)
        
        return updated_links
    
    async def reset_to_default(self) -> List[SocialLink]:
        """Reset all social links to default values"""
        # Delete all existing links
        await SocialLink.delete_all()
        
        # Create default links
        default_links = SocialLink.get_default_links()
        for link in default_links:
            await link.create()
        
        return default_links
    
    async def validate_create(self, obj_in: SocialLinkCreate) -> None:
        """Validate social link creation"""
        # Check if platform already exists
        existing = await self.get_social_link_by_platform(obj_in.platform)
        if existing:
            raise ValueError(f"Social link for platform '{obj_in.platform}' already exists")
    
    async def validate_update(self, social_link_id: str, obj_in: SocialLinkUpdate) -> None:
        """Validate social link update"""
        # Check if platform name is being changed and if it conflicts
        if obj_in.platform:
            existing = await self.get_social_link_by_platform(obj_in.platform)
            if existing and str(existing.id) != social_link_id:
                raise ValueError(f"Social link for platform '{obj_in.platform}' already exists")
