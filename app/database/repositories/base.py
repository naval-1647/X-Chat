"""
Base repository class for ChatX API
"""
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from bson import ObjectId
from beanie import Document
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

from app.database.__init__db import get_mongodb_client
from app.config import db_settings

T = TypeVar('T', bound=Document)


class BaseRepository(Generic[T]):
    """Base repository class with common database operations"""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
        self.collection_name = model_class.Settings.name
    
    @property
    def collection(self):
        """Get MongoDB collection"""
        client = get_mongodb_client()
        return client[db_settings.DATABASE_NAME][self.collection_name]
    
    async def create(self, **kwargs) -> T:
        """Create a new document"""
        document = self.model_class(**kwargs)
        await document.insert()
        return document
    
    async def get_by_id(self, document_id: str) -> Optional[T]:
        """Get document by ID"""
        if not ObjectId.is_valid(document_id):
            return None
        return await self.model_class.get(ObjectId(document_id))
    
    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get document by field value"""
        return await self.model_class.find_one({field: value})
    
    async def get_many_by_field(self, field: str, value: Any, limit: int = 100) -> List[T]:
        """Get multiple documents by field value"""
        return await self.model_class.find({field: value}).limit(limit).to_list()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all documents with pagination"""
        return await self.model_class.find_all().skip(skip).limit(limit).to_list()
    
    async def update_by_id(self, document_id: str, **kwargs) -> Optional[T]:
        """Update document by ID"""
        if not ObjectId.is_valid(document_id):
            return None
        
        document = await self.get_by_id(document_id)
        if not document:
            return None
        
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        document.updated_at = datetime.utcnow()
        await document.save()
        return document
    
    async def delete_by_id(self, document_id: str) -> bool:
        """Delete document by ID"""
        if not ObjectId.is_valid(document_id):
            return False
        
        document = await self.get_by_id(document_id)
        if not document:
            return False
        
        await document.delete()
        return True
    
    async def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching filter"""
        if filter_dict:
            return await self.model_class.find(filter_dict).count()
        return await self.model_class.count()
    
    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """Check if document exists"""
        count = await self.model_class.find(filter_dict).limit(1).count()
        return count > 0
    
    async def find_with_pagination(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        sort_field: str = "created_at",
        sort_direction: int = DESCENDING,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Find documents with pagination"""
        skip = (page - 1) * limit
        
        query = self.model_class.find(filter_dict or {})
        
        # Get total count
        total = await query.count()
        
        # Get documents
        documents = await query.sort([(sort_field, sort_direction)]).skip(skip).limit(limit).to_list()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "items": documents,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        }
    
    async def bulk_create(self, documents_data: List[Dict[str, Any]]) -> List[T]:
        """Create multiple documents"""
        documents = [self.model_class(**data) for data in documents_data]
        await self.model_class.insert_many(documents)
        return documents
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update documents"""
        if not updates:
            return 0
        
        operations = []
        for update in updates:
            document_id = update.pop('id', None)
            if document_id and ObjectId.is_valid(document_id):
                operations.append({
                    'updateOne': {
                        'filter': {'_id': ObjectId(document_id)},
                        'update': {'$set': {**update, 'updated_at': datetime.utcnow()}}
                    }
                })
        
        if operations:
            result = await self.collection.bulk_write(operations)
            return result.modified_count
        
        return 0
    
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)