"""
StudySprint 4.0 - Shared Database Utilities
Common database operations and utilities
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any, Type, TypeVar
from datetime import datetime, timedelta
import logging

from database import SessionLocal

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class DatabaseService:
    """Base database service with common operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def create(self, db: Session, **kwargs) -> ModelType:
        """Create new record"""
        try:
            obj = self.model(**kwargs)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            logger.info(f"✅ Created {self.model.__name__} with ID {obj.id}")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create {self.model.__name__}: {e}")
            raise
    
    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        """Get record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with pagination and filtering"""
        query = db.query(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                query = query.order_by(desc(getattr(self.model, order_by[1:])))
            else:
                query = query.order_by(asc(getattr(self.model, order_by)))
        
        return query.offset(skip).limit(limit).all()
    
    def update(self, db: Session, id: int, **kwargs) -> Optional[ModelType]:
        """Update record by ID"""
        try:
            obj = self.get_by_id(db, id)
            if not obj:
                return None
            
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(obj)
            logger.info(f"✅ Updated {self.model.__name__} with ID {id}")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to update {self.model.__name__} {id}: {e}")
            raise
    
    def delete(self, db: Session, id: int) -> bool:
        """Delete record by ID"""
        try:
            obj = self.get_by_id(db, id)
            if not obj:
                return False
            
            db.delete(obj)
            db.commit()
            logger.info(f"✅ Deleted {self.model.__name__} with ID {id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to delete {self.model.__name__} {id}: {e}")
            raise
    
    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()


def init_database():
    """Initialize database - imported from main database module"""
    from database import init_database as _init_database
    return _init_database()
