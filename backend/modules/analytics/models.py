# backend/modules/analytics/models.py
"""
StudySprint 4.0 - Analytics Models
SQLAlchemy models for advanced session analytics
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from database import Base


class FocusLevel(str, Enum):
    """Focus level enumeration"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    VERY_HIGH = "very_high"


class ProductivityTrend(str, Enum):
    """Productivity trend enumeration"""
    DECLINING = "declining"
    STABLE = "stable"
    IMPROVING = "improving"
    FLUCTUATING = "fluctuating"


class SessionAnalytics(Base):
    """Enhanced session analytics model"""
    __tablename__ = "session_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, unique=True)
    
    # Focus analysis
    focus_periods = Column(JSON, default=list)  # List of focus period data
    distraction_events = Column(JSON, default=list)  # Distraction incidents
    focus_score = Column(Float, default=0.0)  # 0.0 to 1.0
    average_focus_duration = Column(Float, default=0.0)  # minutes
    
    # Productivity metrics
    productivity_score = Column(Float, default=0.0)  # 0.0 to 1.0
    efficiency_rating = Column(String(20), default="medium")
    pages_per_minute_actual = Column(Float, default=0.0)
    pages_per_minute_target = Column(Float, default=1.0)
    
    # Break pattern analysis
    break_frequency_score = Column(Float, default=0.5)  # Optimal = 1.0
    break_duration_average = Column(Float, default=0.0)  # minutes
    break_timing_score = Column(Float, default=0.5)  # How well-timed breaks are
    
    # Performance indicators
    consistency_score = Column(Float, default=0.5)
    improvement_indicators = Column(JSON, default=dict)
    fatigue_indicators = Column(JSON, default=dict)
    
    # Recommendations generated
    optimization_suggestions = Column(JSON, default=list)
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", backref="analytics")
    page_analytics = relationship("PageAnalytics", back_populates="session_analytics")
    
    def __repr__(self):
        return f"<SessionAnalytics(session_id={self.session_id}, focus={self.focus_score:.2f}, productivity={self.productivity_score:.2f})>"


class PageAnalytics(Base):
    """Page-level analytics model"""
    __tablename__ = "page_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    session_analytics_id = Column(Integer, ForeignKey("session_analytics.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    
    # Reading efficiency
    reading_efficiency = Column(Float, default=0.5)  # 0.0 to 1.0
    time_spent_seconds = Column(Integer, default=0)
    optimal_time_seconds = Column(Integer, default=60)
    
    # Difficulty assessment
    difficulty_score = Column(Float, default=0.5)  # 0.0 to 1.0 (auto-calculated)
    user_perceived_difficulty = Column(Float, nullable=True)  # User rating
    
    # Engagement metrics
    revisit_count = Column(Integer, default=0)
    highlight_count = Column(Integer, default=0)
    note_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    
    # Performance indicators
    reading_speed_variance = Column(Float, default=0.0)
    focus_interruptions = Column(Integer, default=0)
    effective_reading_time = Column(Integer, default=0)  # seconds
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session_analytics = relationship("SessionAnalytics", back_populates="page_analytics")
    
    def calculate_engagement_score(self):
        """Calculate engagement score based on interactions"""
        base_score = 0.0
        
        # Highlights contribute to engagement
        if self.highlight_count > 0:
            base_score += min(0.4, self.highlight_count * 0.1)
        
        # Notes show deeper engagement
        if self.note_count > 0:
            base_score += min(0.3, self.note_count * 0.15)
        
        # Revisits can indicate both difficulty and engagement
        if self.revisit_count > 0:
            base_score += min(0.3, self.revisit_count * 0.1)
        
        self.engagement_score = min(1.0, base_score)


class PerformanceMetrics(Base):
    """User performance metrics over time"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Daily metrics
    total_study_time_minutes = Column(Integer, default=0)
    total_active_time_minutes = Column(Integer, default=0)
    total_pages_covered = Column(Integer, default=0)
    session_count = Column(Integer, default=0)
    
    # Performance indicators
    average_focus_score = Column(Float, default=0.0)
    average_productivity_score = Column(Float, default=0.0)
    average_reading_speed = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    
    # Trend analysis
    productivity_trend = Column(String(20), default=ProductivityTrend.STABLE.value)
    focus_trend = Column(String(20), default=ProductivityTrend.STABLE.value)
    speed_trend = Column(String(20), default=ProductivityTrend.STABLE.value)
    
    # Comparative metrics
    efficiency_vs_previous_day = Column(Float, default=0.0)  # -1.0 to 1.0
    improvement_indicators = Column(JSON, default=dict)
    
    # Goals and targets
    daily_target_minutes = Column(Integer, default=120)  # 2 hours default
    target_achievement_rate = Column(Float, default=0.0)
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PerformanceMetrics(date={self.date.date()}, study_time={self.total_study_time_minutes}m)>"