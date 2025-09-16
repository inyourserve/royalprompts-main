"""
Admin Panel Category Management Endpoints
Handles CRUD operations for categories in admin panel
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.admin_auth import get_current_admin
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryAdmin
from app.schemas.common import PaginationParams
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("", tags=["Admin Categories"])
async def get_admin_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_admin = Depends(get_current_admin)
):
    """Get categories for admin management"""
    category_service = CategoryService()
    pagination = PaginationParams(skip=(page-1)*limit, limit=limit)
    
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    
    if search:
        categories = await category_service.search(search, limit=limit)
        total = len(categories)
    else:
        result = await category_service.get_multi(pagination, filters)
        categories = result.items
        total = result.total
    
    admin_categories = []
    for category in categories:
        category_dict = category.model_dump()
        category_dict["id"] = str(category.id)
        # Remove any slug field if present (legacy data cleanup)
        category_dict.pop("slug", None)
        admin_categories.append(CategoryAdmin.model_validate(category_dict))
    
    return {"items": admin_categories, "total": total, "page": page, "limit": limit}


@router.get("/{category_id}", tags=["Admin Categories"])
async def get_admin_category(
    category_id: str,
    current_admin = Depends(get_current_admin)
):
    """Get single category by ID"""
    category_service = CategoryService()
    category = await category_service.get_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_dict = category.model_dump()
    category_dict["id"] = str(category.id)
    # Remove any slug field if present (legacy data cleanup)
    category_dict.pop("slug", None)
    return CategoryAdmin.model_validate(category_dict)


@router.post("", tags=["Admin Categories"])
async def create_admin_category(
    category_in: CategoryCreate,
    current_admin = Depends(get_current_admin)
):
    """Create new category"""
    category_service = CategoryService()
    category_data = category_in.model_dump()
    category_data["created_by"] = str(current_admin.id)
    
    category = await category_service.create(category_data)
    category_dict = category.model_dump()
    category_dict["id"] = str(category.id)
    # Remove any slug field if present (legacy data cleanup)
    category_dict.pop("slug", None)
    return CategoryAdmin.model_validate(category_dict)


@router.put("/{category_id}", tags=["Admin Categories"])
async def update_admin_category(
    category_id: str,
    category_in: CategoryUpdate,
    current_admin = Depends(get_current_admin)
):
    """Update category"""
    category_service = CategoryService()
    update_data = category_in.model_dump(exclude_unset=True)
    updated_category = await category_service.update(category_id, update_data)
    
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_dict = updated_category.model_dump()
    category_dict["id"] = str(updated_category.id)
    # Remove any slug field if present (legacy data cleanup)
    category_dict.pop("slug", None)
    return CategoryAdmin.model_validate(category_dict)


@router.delete("/{category_id}", tags=["Admin Categories"])
async def delete_admin_category(
    category_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete category"""
    category_service = CategoryService()
    success = await category_service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


@router.post("/{category_id}/toggle-status", tags=["Admin Categories"])
async def toggle_category_status(
    category_id: str,
    current_admin = Depends(get_current_admin)
):
    """Toggle category active status"""
    category_service = CategoryService()
    category = await category_service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated_category = await category_service.update(
        category_id, 
        {"is_active": not category.is_active}
    )
    
    category_dict = updated_category.model_dump()
    category_dict["id"] = str(updated_category.id)
    # Remove any slug field if present (legacy data cleanup)
    category_dict.pop("slug", None)
    return CategoryAdmin.model_validate(category_dict)
