from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from beanie import Document, PydanticObjectId

T = TypeVar("T", bound=Document)


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for database operations"""
    
    def __init__(self, model: T):
        self.model = model
    
    @abstractmethod
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new document"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get document by ID"""
        pass
    
    @abstractmethod
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple documents with pagination"""
        pass
    
    @abstractmethod
    async def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update document by ID"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete document by ID"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents"""
        pass


class MongoRepository(BaseRepository[T]):
    """MongoDB repository implementation using Beanie"""
    
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new document"""
        obj = self.model(**obj_in)
        await obj.create()
        return obj
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get document by ID"""
        try:
            return await self.model.get(PydanticObjectId(id))
        except Exception:
            return None
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: int = 1
    ) -> List[T]:
        """Get multiple documents with pagination"""
        query = {}
        if filters:
            query.update(filters)
        
        find_query = self.model.find(query).skip(skip).limit(limit)
        
        if sort_by:
            sort_criteria = [(sort_by, sort_order)]
            find_query = find_query.sort(sort_criteria)
        
        return await find_query.to_list()
    
    async def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update document by ID"""
        obj = await self.get_by_id(id)
        if not obj:
            return None
        
        for field, value in obj_in.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        await obj.save()
        return obj
    
    async def delete(self, id: str) -> bool:
        """Delete document by ID"""
        obj = await self.get_by_id(id)
        if not obj:
            return False
        
        await obj.delete()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents"""
        query = {}
        if filters:
            query.update(filters)
        
        return await self.model.find(query).count()
    
    async def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """Find one document by filters"""
        return await self.model.find_one(filters)
    
    async def find_many(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """Find many documents by filters"""
        query = self.model.find(filters)
        if limit:
            query = query.limit(limit)
        return await query.to_list()


class CacheableRepository(MongoRepository[T]):
    """Repository with caching capabilities"""
    
    def __init__(self, model: T, cache_ttl: int = 300):
        super().__init__(model)
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get document by ID with caching"""
        # Check cache first
        if id in self._cache:
            return self._cache[id]
        
        # Get from database
        obj = await super().get_by_id(id)
        if obj:
            self._cache[id] = obj
        
        return obj
    
    def clear_cache(self, id: Optional[str] = None) -> None:
        """Clear cache for specific ID or all"""
        if id:
            self._cache.pop(id, None)
        else:
            self._cache.clear()
