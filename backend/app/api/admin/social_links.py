"""
Admin Social Links API Endpoints
Handles social media links management for admin panel
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import get_current_admin
from app.schemas.social_link import (
    SocialLinkResponse, 
    SocialLinkCreate,
    SocialLinkUpdate,
    SocialLinksListResponse,
    SocialLinksBulkUpdate
)
from app.services.social_link_service import SocialLinkService

router = APIRouter()


@router.get("/", response_model=SocialLinksListResponse, tags=["Admin Social Links"])
async def get_social_links(current_admin = Depends(get_current_admin)):
    """Get all social links"""
    social_link_service = SocialLinkService()
    links = await social_link_service.get_all_social_links()
    
    # Convert to response format
    response_links = []
    for link in links:
        link_dict = link.model_dump()
        link_dict["id"] = str(link.id)
        response_links.append(SocialLinkResponse.model_validate(link_dict))
    
    return SocialLinksListResponse(
        items=response_links,
        total=len(response_links)
    )


@router.get("/active", response_model=SocialLinksListResponse, tags=["Admin Social Links"])
async def get_active_social_links(current_admin = Depends(get_current_admin)):
    """Get only active social links"""
    social_link_service = SocialLinkService()
    links = await social_link_service.get_active_social_links()
    
    # Convert to response format
    response_links = []
    for link in links:
        link_dict = link.model_dump()
        link_dict["id"] = str(link.id)
        response_links.append(SocialLinkResponse.model_validate(link_dict))
    
    return SocialLinksListResponse(
        items=response_links,
        total=len(response_links)
    )


@router.post("/", response_model=SocialLinkResponse, tags=["Admin Social Links"])
async def create_social_link(
    link_data: SocialLinkCreate,
    current_admin = Depends(get_current_admin)
):
    """Create a new social link"""
    social_link_service = SocialLinkService()
    
    try:
        await social_link_service.validate_create(link_data)
        new_link = await social_link_service.create(link_data)
        
        # Convert to response format
        link_dict = new_link.model_dump()
        link_dict["id"] = str(new_link.id)
        return SocialLinkResponse.model_validate(link_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create social link: {str(e)}"
        )


@router.put("/bulk", response_model=SocialLinksListResponse, tags=["Admin Social Links"])
async def bulk_update_social_links(
    bulk_data: SocialLinksBulkUpdate,
    current_admin = Depends(get_current_admin)
):
    """Bulk update social links"""
    social_link_service = SocialLinkService()
    
    try:
        updated_links = await social_link_service.bulk_update_social_links(bulk_data.links)
        
        # Convert to response format
        response_links = []
        for link in updated_links:
            link_dict = link.model_dump()
            link_dict["id"] = str(link.id)
            response_links.append(SocialLinkResponse.model_validate(link_dict))
        
        return SocialLinksListResponse(
            items=response_links,
            total=len(response_links)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update social links: {str(e)}"
        )


@router.put("/{link_id}", response_model=SocialLinkResponse, tags=["Admin Social Links"])
async def update_social_link(
    link_id: str,
    link_data: SocialLinkUpdate,
    current_admin = Depends(get_current_admin)
):
    """Update a specific social link"""
    social_link_service = SocialLinkService()
    
    try:
        await social_link_service.validate_update(link_id, link_data)
        updated_link = await social_link_service.update(link_id, link_data)
        
        if not updated_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social link not found"
            )
        
        # Convert to response format
        link_dict = updated_link.model_dump()
        link_dict["id"] = str(updated_link.id)
        return SocialLinkResponse.model_validate(link_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update social link: {str(e)}"
        )


@router.delete("/{link_id}", tags=["Admin Social Links"])
async def delete_social_link(
    link_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete a social link"""
    social_link_service = SocialLinkService()
    
    try:
        success = await social_link_service.delete(link_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social link not found"
            )
        
        return {"message": "Social link deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete social link: {str(e)}"
        )


@router.post("/reset", response_model=SocialLinksListResponse, tags=["Admin Social Links"])
async def reset_social_links(current_admin = Depends(get_current_admin)):
    """Reset social links to default values"""
    social_link_service = SocialLinkService()
    
    try:
        default_links = await social_link_service.reset_to_default()
        
        # Convert to response format
        response_links = []
        for link in default_links:
            link_dict = link.model_dump()
            link_dict["id"] = str(link.id)
            response_links.append(SocialLinkResponse.model_validate(link_dict))
        
        return SocialLinksListResponse(
            items=response_links,
            total=len(response_links)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset social links: {str(e)}"
        )
