"""
StudySprint 4.0 - Shared Type Definitions
Common type definitions across modules
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class StudyType(str, Enum):
    """Types of study content"""
    STUDY = "study"
    EXERCISE = "exercise"
    REVIEW = "review"
    PRACTICE = "practice"


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Difficulty(str, Enum):
    """Difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# Base response models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    items: List[Any]
    pagination: PaginationMetadata


# Progress tracking
class ProgressInfo(BaseModel):
    """Progress information"""
    completed: int
    total: int
    percentage: float
    estimated_completion: Optional[datetime] = None


# Analytics data structures
class TimeDistribution(BaseModel):
    """Time distribution analytics"""
    total_time: int
    active_time: int
    break_time: int
    efficiency_percentage: float


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    average_session_duration: int
    total_study_time: int
    completion_rate: float
    focus_score: float
    productivity_trend: str  # "improving", "declining", "stable"


# File information
class FileInfo(BaseModel):
    """File information structure"""
    filename: str
    size: int
    content_type: str
    upload_time: datetime
    hash: str
    path: str


# Session analytics
class SessionAnalytics(BaseModel):
    """Session analytics data"""
    duration: int
    pages_covered: int
    reading_speed: float
    focus_periods: List[Dict[str, Any]]
    break_periods: List[Dict[str, Any]]
    effectiveness_score: float
