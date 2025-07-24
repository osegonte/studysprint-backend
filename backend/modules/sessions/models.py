"""
StudySprint 4.0 - Session Models
SQLAlchemy models for study sessions with real-time tracking
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from database import Base


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionType(str, Enum):
    """Session type enumeration"""
    STUDY = "study"
    EXERCISE = "exercise"
    REVIEW = "review"
    PRACTICE = "practice"


class Session(Base):
    """Study session model with real-time tracking"""
    __tablename__ = "sessions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    session_type = Column(String(20), default=SessionType.STUDY.value)
    status = Column(String(20), default=SessionStatus.ACTIVE.value)
    
    # Foreign keys
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=True)
    
    # Session timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    pause_time = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Integer, default=0)
    active_duration_seconds = Column(Integer, default=0)
    break_duration_seconds = Column(Integer, default=0)
    
    # Page tracking
    current_page = Column(Integer, default=1)
    start_page = Column(Integer, default=1)
    end_page = Column(Integer, nullable=True)
    pages_covered = Column(Integer, default=0)
    
    # Analytics
    focus_score = Column(Float, default=0.0)
    productivity_score = Column(Float, default=0.0)
    reading_speed = Column(Float, default=0.0)  # pages per minute
    
    # Session notes and goals
    session_goal = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Metadata
    page_times = Column(JSON, default=list)  # List of page timing data
    break_periods = Column(JSON, default=list)  # List of break periods
    activity_log = Column(JSON, default=list)  # Activity tracking
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pdf = relationship("PDF", back_populates="sessions")
    estimation_records = relationship("EstimationHistory", back_populates="session")
    analytics = relationship("SessionAnalytics", back_populates="session", uselist=False)
    def __repr__(self):
        return f"<Session(id={self.id}, type={self.session_type}, status={self.status})>"
    
    def calculate_metrics(self):
        """Calculate session metrics"""
        if self.total_duration_seconds > 0:
            # Reading speed (pages per minute)
            minutes = self.active_duration_seconds / 60
            if minutes > 0:
                self.reading_speed = self.pages_covered / minutes
            
            # Productivity score (active time / total time)
            self.productivity_score = (self.active_duration_seconds / self.total_duration_seconds) * 100
        
        self.updated_at = datetime.utcnow()


class PageTime(Base):
    """Page-level timing data"""
    __tablename__ = "page_times"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    reading_speed = Column(Float, default=0.0)
    revisited = Column(Boolean, default=False)
    
    # Relationship
    session = relationship("Session", backref="page_timing_details")
    
    def __repr__(self):
        return f"<PageTime(session_id={self.session_id}, page={self.page_number}, duration={self.duration_seconds}s)>"