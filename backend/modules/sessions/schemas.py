"""
StudySprint 4.0 - Session Schemas
Pydantic models for session API validation
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionType(str, Enum):
    STUDY = "study"
    EXERCISE = "exercise"
    REVIEW = "review"
    PRACTICE = "practice"


class SessionCreate(BaseModel):
    """Schema for creating a session"""
    session_type: SessionType = SessionType.STUDY
    topic_id: Optional[int] = None
    pdf_id: Optional[int] = None
    start_page: int = Field(1, ge=1)
    session_goal: Optional[str] = Field(None, max_length=500)


class SessionUpdate(BaseModel):
    """Schema for updating a session"""
    current_page: Optional[int] = Field(None, ge=1)
    end_page: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = Field(None, max_length=1000)
    session_goal: Optional[str] = Field(None, max_length=500)


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: int
    session_type: SessionType
    status: SessionStatus
    topic_id: Optional[int]
    pdf_id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: int
    active_duration_seconds: int
    break_duration_seconds: int
    current_page: int
    start_page: int
    end_page: Optional[int]
    pages_covered: int
    focus_score: float
    productivity_score: float
    reading_speed: float
    session_goal: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """Schema for session summary"""
    id: int
    session_type: SessionType
    status: SessionStatus
    duration_formatted: str
    pages_covered: int
    reading_speed: float
    productivity_score: float
    focus_score: float
    start_time: datetime
    end_time: Optional[datetime]


class PageTimeCreate(BaseModel):
    """Schema for logging page time"""
    page_number: int = Field(..., ge=1)
    duration_seconds: int = Field(..., ge=0)
    reading_speed: Optional[float] = Field(None, ge=0)


class PageTimeResponse(BaseModel):
    """Schema for page time response"""
    id: int
    session_id: int
    page_number: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int
    reading_speed: float
    revisited: bool
    
    class Config:
        from_attributes = True


class TimerUpdate(BaseModel):
    """Schema for WebSocket timer updates"""
    session_id: int
    current_time: datetime
    elapsed_seconds: int
    status: SessionStatus
    current_page: Optional[int] = None


class SessionAnalytics(BaseModel):
    """Schema for session analytics"""
    total_sessions: int
    total_study_time: int
    average_session_duration: int
    average_pages_per_session: float
    average_reading_speed: float
    productivity_trend: str
    focus_trend: str
    most_productive_hours: List[int]
    session_distribution: Dict[str, int]