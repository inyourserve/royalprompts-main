from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from app.db.base import BaseRepository
from app.schemas.common import PaginationParams, PaginatedResponse

T = TypeVar("T")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(ABC, Generic[T, CreateSchemaType, UpdateSchemaType]):
    """Abstract base service class"""
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
    
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create a new object"""
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        return await self.repository.create(obj_data)
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get object by ID"""
        return await self.repository.get_by_id(id)
    
    async def get_multi(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: int = 1
    ) -> PaginatedResponse[T]:
        """Get multiple objects with pagination"""
        # Get total count
        total = await self.repository.count(filters)
        
        # Get items
        items = await self.repository.get_multi(
            skip=pagination.skip,
            limit=pagination.limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return PaginatedResponse.create(items, total, pagination)
    
    async def update(self, id: str, obj_in: UpdateSchemaType) -> Optional[T]:
        """Update object"""
        obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        return await self.repository.update(id, obj_data)
    
    async def delete(self, id: str) -> bool:
        """Delete object"""
        return await self.repository.delete(id)
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count objects"""
        return await self.repository.count(filters)
    
    @abstractmethod
    async def validate_create(self, obj_in: CreateSchemaType) -> None:
        """Validate object creation"""
        pass
    
    @abstractmethod
    async def validate_update(self, id: str, obj_in: UpdateSchemaType) -> None:
        """Validate object update"""
        pass
