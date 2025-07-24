"""
StudySprint 4.0 - Topics Service
Business logic for topics management
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from shared.database import DatabaseService
from .models import Topic
from .schemas import TopicCreate, TopicUpdate
from core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class TopicsService(DatabaseService):
    """Service class for topics management"""
    
    def __init__(self):
        super().__init__(Topic)
    
    def create_topic(self, db: Session, topic_data: TopicCreate) -> Topic:
        """Create a new topic"""
        try:
            # Check for duplicate names
            existing = db.query(Topic).filter(Topic.name == topic_data.name).first()
            if existing:
                raise ValidationException(f"Topic with name '{topic_data.name}' already exists")
            
            topic = Topic(
                name=topic_data.name,
                description=topic_data.description,
                color=topic_data.color,
                priority=topic_data.priority,
                estimated_hours=topic_data.estimated_hours or 0.0
            )
            
            db.add(topic)
            db.commit()
            db.refresh(topic)
            
            logger.info(f"✅ Created topic: {topic.name}")
            return topic
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create topic: {e}")
            raise
    
    def get_topics(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Topic], int]:
        """Get topics with filtering and pagination"""
        query = db.query(Topic)
        
        # Apply filters
        if active_only:
            query = query.filter(Topic.is_active == True, Topic.is_archived == False)
        
        if priority:
            query = query.filter(Topic.priority == priority)
        
        if search:
            query = query.filter(Topic.name.ilike(f"%{search}%"))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        topics = query.order_by(Topic.updated_at.desc()).offset(skip).limit(limit).all()
        
        return topics, total
    
    def get_topic_by_id(self, db: Session, topic_id: int) -> Topic:
        """Get topic by ID"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise NotFoundException("Topic", topic_id)
        return topic
    
    def update_topic(self, db: Session, topic_id: int, topic_data: TopicUpdate) -> Topic:
        """Update topic"""
        try:
            topic = self.get_topic_by_id(db, topic_id)
            
            # Check for name conflicts if name is being updated
            if topic_data.name and topic_data.name != topic.name:
                existing = db.query(Topic).filter(
                    Topic.name == topic_data.name,
                    Topic.id != topic_id
                ).first()
                if existing:
                    raise ValidationException(f"Topic with name '{topic_data.name}' already exists")
            
            # Update fields
            update_data = topic_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(topic, field, value)
            
            topic.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(topic)
            
            logger.info(f"✅ Updated topic: {topic.name}")
            return topic
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to update topic {topic_id}: {e}")
            raise
    
    def delete_topic(self, db: Session, topic_id: int) -> bool:
        """Delete topic (soft delete by archiving)"""
        try:
            topic = self.get_topic_by_id(db, topic_id)
            
            # Soft delete by archiving
            topic.is_archived = True
            topic.is_active = False
            topic.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"✅ Archived topic: {topic.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to delete topic {topic_id}: {e}")
            raise
    
    def get_topic_progress(self, db: Session, topic_id: int) -> Dict[str, Any]:
        """Get detailed progress analytics for a topic"""
        topic = self.get_topic_by_id(db, topic_id)
        
        # Calculate reading speed
        pages_per_hour = 0.0
        if topic.actual_hours > 0:
            pages_per_hour = topic.completed_pages / topic.actual_hours
        
        # Estimate completion date
        estimated_completion_date = None
        if pages_per_hour > 0 and topic.total_pages > topic.completed_pages:
            remaining_pages = topic.total_pages - topic.completed_pages
            remaining_hours = remaining_pages / pages_per_hour
            estimated_completion_date = datetime.utcnow() + timedelta(hours=remaining_hours)
        
        # Calculate study streak (simplified for now)
        study_streak_days = 0
        if topic.last_studied_at:
            days_since_study = (datetime.utcnow() - topic.last_studied_at).days
            if days_since_study <= 1:
                study_streak_days = 1  # Simplified calculation
        
        return {
            "id": topic.id,
            "name": topic.name,
            "total_pages": topic.total_pages,
            "completed_pages": topic.completed_pages,
            "completion_percentage": topic.completion_percentage,
            "estimated_hours": topic.estimated_hours,
            "actual_hours": topic.actual_hours,
            "pages_per_hour": pages_per_hour,
            "estimated_completion_date": estimated_completion_date,
            "study_streak_days": study_streak_days,
            "last_studied_at": topic.last_studied_at
        }
    
    def update_progress(self, db: Session, topic_id: int, completed_pages: int) -> Topic:
        """Update topic progress"""
        try:
            topic = self.get_topic_by_id(db, topic_id)
            topic.completed_pages = max(0, min(completed_pages, topic.total_pages))
            topic.update_progress()
            
            db.commit()
            db.refresh(topic)
            
            logger.info(f"✅ Updated progress for topic {topic.name}: {topic.completion_percentage}%")
            return topic
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to update progress for topic {topic_id}: {e}")
            raise


# Global service instance
topics_service = TopicsService()