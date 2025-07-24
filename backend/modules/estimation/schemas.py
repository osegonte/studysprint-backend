# backend/modules/estimation/schemas.py
"""
StudySprint 4.0 - Estimation Schemas
Pydantic models for estimation API validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ContentType(str, Enum):
    PDF = "pdf"
    TOPIC = "topic"
    EXERCISE = "exercise"
    PAGE = "page"


class EstimationConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EstimationCreate(BaseModel):
    """Schema for creating estimation"""
    content_type: ContentType
    content_id: int = Field(..., gt=0)
    user_context: Optional[Dict[str, Any]] = None


class EstimationUpdate(BaseModel):
    """Schema for updating estimation"""
    estimated_time_minutes: Optional[float] = Field(None, gt=0)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    user_context: Optional[Dict[str, Any]] = None


class EstimationResponse(BaseModel):
    """Schema for estimation response"""
    id: int
    content_type: ContentType
    content_id: int
    estimated_time_minutes: float
    estimated_time_formatted: str
    confidence_score: float
    confidence_level: EstimationConfidence
    estimation_factors: Dict[str, Any]
    algorithm_version: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PDFEstimationResponse(BaseModel):
    """Schema for PDF-specific estimation response"""
    pdf_id: int
    estimated_time_minutes: float
    estimated_time_formatted: str
    confidence_score: float
    confidence_level: EstimationConfidence
    factors: Dict[str, Any]
    estimation_id: int
    page_count: int
    estimated_pages_per_minute: float
    completion_date_estimate: datetime


class TopicEstimationResponse(BaseModel):
    """Schema for topic estimation response"""
    topic_id: int
    topic_name: str
    estimated_time_minutes: float
    estimated_time_formatted: str
    confidence_score: float
    confidence_level: EstimationConfidence
    pdf_count: int
    pdf_estimates: List[PDFEstimationResponse]
    completion_date_estimate: datetime
    remaining_pages: float


class AppTotalEstimationResponse(BaseModel):
    """Schema for app-wide estimation response"""
    total_estimated_time_minutes: float
    total_estimated_time_formatted: str
    confidence_score: float
    confidence_level: EstimationConfidence
    topic_count: int
    total_pages: int
    completed_pages: int
    completion_percentage: float
    estimated_completion_date: datetime
    topic_estimates: List[TopicEstimationResponse]
    daily_study_recommendation: Dict[str, Any]


class EstimationAccuracyResponse(BaseModel):
    """Schema for estimation accuracy analytics"""
    overall_accuracy: float
    accuracy_standard_deviation: float
    sample_size: int
    accuracy_by_content_type: Dict[str, float]
    trend: str
    confidence_level: str


class SessionEstimationUpdate(BaseModel):
    """Schema for session-based estimation update"""
    session_id: int
    actual_time_minutes: float
    reading_speed: float
    patterns_updated: bool
    estimations_recalculated: int
    updated_estimations: List[Dict[str, Any]]