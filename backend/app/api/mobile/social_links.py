"""
Mobile Social Links API Endpoints
Public endpoints for social media links
"""
from fastapi import APIRouter
from app.schemas.social_link import SocialLinksPublicListResponse, SocialLinkPublic
from app.services.social_link_service import SocialLinkService

router = APIRouter()


@router.get("/", response_model=SocialLinksPublicListResponse, tags=["Mobile Social Links"])
async def get_public_social_links():
    """Get active social links for public display"""
    social_link_service = SocialLinkService()
    links = await social_link_service.get_active_social_links()
    
    # Convert to public format (no sensitive data)
    response_links = []
    for link in links:
        response_links.append(SocialLinkPublic(
            platform=link.platform,
            url=str(link.url),  # Convert HttpUrl to string
            is_active=link.is_active,
            display_order=link.display_order
        ))
    
    return SocialLinksPublicListResponse(
        items=response_links,
        total=len(response_links)
    )
