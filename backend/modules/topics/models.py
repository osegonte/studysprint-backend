"""
StudySprint 4.0 - Topic Models
SQLAlchemy models for topics with progress tracking
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Topic(Base):
    """Topic model with progress tracking"""
    __tablename__ = "topics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3B82F6")  # Hex color code
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Progress tracking
    total_pages = Column(Integer, default=0)
    completed_pages = Column(Integer, default=0)
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_studied_at = Column(DateTime, nullable=True)
    
    # Relationships (will be added as other modules are implemented)
    # pdfs = relationship("PDF", back_populates="topic")
    # sessions = relationship("Session", back_populates="topic")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}', progress={self.completion_percentage}%)>"
    
    def update_progress(self):
        """Update completion percentage based on completed/total pages"""
        if self.total_pages > 0:
            self.completion_percentage = (self.completed_pages / self.total_pages) * 100
        else:
            self.completion_percentage = 0.0
        self.updated_at = datetime.utcnow()
    
    def add_study_time(self, hours: float):
        """Add study time and update last studied timestamp"""
        self.actual_hours += hours
        self.last_studied_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()