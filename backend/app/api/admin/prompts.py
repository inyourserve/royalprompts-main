"""
Admin Panel Prompts Management Endpoints
Handles CRUD operations for prompts and image uploads in admin panel
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from app.core.admin_auth import get_current_admin
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptAdmin
from app.schemas.common import PaginationParams, ImageUploadResponse
from app.services.prompt_service import PromptService
from app.utils.file_upload import get_file_upload_manager

router = APIRouter()


@router.get("", tags=["Admin Prompts"])
async def get_admin_prompts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_admin = Depends(get_current_admin)
):
    """Get prompts for admin table"""
    prompt_service = PromptService()
    pagination = PaginationParams(skip=(page-1)*limit, limit=limit)
    
    filters = {}
    if category_id:
        filters["category_id"] = category_id
    if status:
        filters["status"] = status
    
    if search:
        prompts = await prompt_service.search(search, limit=limit)
        total = len(prompts)
    else:
        result = await prompt_service.get_multi(pagination, filters)
        prompts = result.items
        total = result.total
    
    admin_prompts = []
    for prompt in prompts:
        prompt_dict = prompt.model_dump()
        prompt_dict["id"] = str(prompt.id)
        admin_prompts.append(PromptAdmin.model_validate(prompt_dict))
    
    return {"items": admin_prompts, "total": total, "page": page, "limit": limit}


@router.get("/{prompt_id}", tags=["Admin Prompts"])
async def get_admin_prompt(
    prompt_id: str,
    current_admin = Depends(get_current_admin)
):
    """Get single prompt by ID"""
    prompt_service = PromptService()
    prompt = await prompt_service.get_by_id(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt_dict = prompt.model_dump()
    prompt_dict["id"] = str(prompt.id)
    return PromptAdmin.model_validate(prompt_dict)


@router.post("", tags=["Admin Prompts"])
async def create_admin_prompt(
    prompt_in: PromptCreate,
    current_admin = Depends(get_current_admin)
):
    """Create new prompt"""
    prompt_service = PromptService()
    prompt_data = prompt_in.model_dump()
    prompt_data["created_by"] = str(current_admin.id)

    prompt = await prompt_service.create(prompt_data)
    prompt_dict = prompt.model_dump()
    prompt_dict["id"] = str(prompt.id)
    return PromptAdmin.model_validate(prompt_dict)


@router.put("/{prompt_id}", tags=["Admin Prompts"])
async def update_admin_prompt(
    prompt_id: str,
    prompt_in: PromptUpdate,
    current_admin = Depends(get_current_admin)
):
    """Update prompt (handles status, featured, etc.)"""
    prompt_service = PromptService()
    update_data = prompt_in.model_dump(exclude_unset=True)
    updated_prompt = await prompt_service.update(prompt_id, update_data)
    
    if not updated_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt_dict = updated_prompt.model_dump()
    prompt_dict["id"] = str(updated_prompt.id)
    return PromptAdmin.model_validate(prompt_dict)


@router.delete("/{prompt_id}", tags=["Admin Prompts"])
async def delete_admin_prompt(
    prompt_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete prompt"""
    prompt_service = PromptService()
    success = await prompt_service.delete(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt deleted successfully"}


@router.post("/upload-image", response_model=ImageUploadResponse, tags=["Admin Prompts"])
async def upload_prompt_image(
    file: UploadFile = File(...),
    current_admin = Depends(get_current_admin),
    file_manager = Depends(get_file_upload_manager)
):
    """
    Upload image for prompt (Admin only)
    Each prompt has exactly 1 image
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    result = await file_manager.save_image(file)
    
    return ImageUploadResponse(
        filename=result["filename"],
        url=result["url"],
        thumbnail_url=result["thumbnail_url"],
        size=result["size"],
        content_type=result["content_type"],
        width=result["width"],
        height=result["height"]
    )
