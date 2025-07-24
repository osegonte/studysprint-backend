# backend/modules/estimation/models.py
"""
StudySprint 4.0 - Estimation Models  
SQLAlchemy models for multi-level time estimation system
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from database import Base


class ContentType(str, Enum):
    """Content type for estimation"""
    PDF = "pdf"
    TOPIC = "topic" 
    EXERCISE = "exercise"
    PAGE = "page"


class EstimationConfidence(str, Enum):
    """Confidence levels for estimates"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EstimationData(Base):
    """Multi-level estimation data model"""
    __tablename__ = "estimation_data"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(20), nullable=False)
    content_id = Column(Integer, nullable=False)
    
    # Estimation values
    estimated_time_minutes = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.5)  # 0.0 to 1.0
    confidence_level = Column(String(20), default=EstimationConfidence.MEDIUM.value)
    
    # Estimation factors
    content_density_factor = Column(Float, default=1.0)
    user_speed_factor = Column(Float, default=1.0)
    difficulty_factor = Column(Float, default=1.0)
    time_of_day_factor = Column(Float, default=1.0)
    
    # Context information
    estimation_factors = Column(JSON, default=dict)
    algorithm_version = Column(String(10), default="1.0")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    history_entries = relationship("EstimationHistory", back_populates="estimation")
    
    def __repr__(self):
        return f"<EstimationData(type={self.content_type}, id={self.content_id}, time={self.estimated_time_minutes}m)>"


class EstimationHistory(Base):
    """Historical estimation accuracy tracking"""
    __tablename__ = "estimation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    estimation_id = Column(Integer, ForeignKey("estimation_data.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Actual vs estimated
    estimated_time_minutes = Column(Float, nullable=False)
    actual_time_minutes = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Performance context
    user_energy_level = Column(Float, default=0.5)  # 0.0 to 1.0
    time_of_day = Column(Integer, nullable=False)  # Hour of day (0-23)
    session_effectiveness = Column(Float, default=0.5)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    estimation = relationship("EstimationData", back_populates="history_entries")
    session = relationship("Session", backref="estimation_records")
    
    def calculate_accuracy(self):
        """Calculate accuracy score based on estimated vs actual time"""
        if self.estimated_time_minutes == 0:
            return 0.0
        
        ratio = min(self.actual_time_minutes, self.estimated_time_minutes) / max(self.actual_time_minutes, self.estimated_time_minutes)
        self.accuracy_score = ratio


class UserReadingPatterns(Base):
    """User reading patterns and performance data"""
    __tablename__ = "user_reading_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(20), nullable=False)
    
    # Reading speed metrics
    average_speed_pages_per_minute = Column(Float, default=1.0)
    peak_speed_pages_per_minute = Column(Float, default=1.5)
    minimum_speed_pages_per_minute = Column(Float, default=0.5)
    
    # Time of day performance
    morning_performance_factor = Column(Float, default=1.0)   # 6-12
    afternoon_performance_factor = Column(Float, default=0.9) # 12-18
    evening_performance_factor = Column(Float, default=0.8)   # 18-24
    night_performance_factor = Column(Float, default=0.6)     # 0-6
    
    # Difficulty adjustments
    beginner_adjustment = Column(Float, default=0.7)
    intermediate_adjustment = Column(Float, default=1.0)
    advanced_adjustment = Column(Float, default=1.3)
    expert_adjustment = Column(Float, default=1.5)
    
    # Pattern analysis
    consistency_score = Column(Float, default=0.5)  # How consistent the user is
    improvement_trend = Column(Float, default=0.0)  # Positive = improving
    total_study_sessions = Column(Integer, default=0)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_time_factor(self, hour: int) -> float:
        """Get performance factor for specific hour"""
        if 6 <= hour < 12:
            return self.morning_performance_factor
        elif 12 <= hour < 18:
            return self.afternoon_performance_factor
        elif 18 <= hour < 24:
            return self.evening_performance_factor
        else:
            return self.night_performance_factor