# backend/modules/analytics/schemas.py
"""
StudySprint 4.0 - Analytics Schemas
Pydantic models for analytics API validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class FocusLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ProductivityTrend(str, Enum):
    DECLINING = "declining"
    STABLE = "stable"
    IMPROVING = "improving"
    FLUCTUATING = "fluctuating"


class SessionAnalyticsResponse(BaseModel):
    """Schema for session analytics response"""
    id: int
    session_id: int
    focus_score: float
    average_focus_duration: float
    productivity_score: float
    efficiency_rating: str
    pages_per_minute_actual: float
    pages_per_minute_target: float
    break_frequency_score: float
    break_duration_average: float
    break_timing_score: float
    optimization_suggestions: List[str]
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class FocusAnalysisResponse(BaseModel):
    """Schema for focus analysis response"""
    session_id: int
    focus_score: float
    total_focus_time_minutes: float
    average_focus_duration_minutes: float
    max_focus_duration_minutes: float
    focus_consistency_score: float
    distraction_count: int
    distraction_frequency_per_hour: float
    focus_periods: List[Dict[str, Any]]
    distraction_events: List[Dict[str, Any]]
    recommendations: List[str]


class ProductivityTrendsResponse(BaseModel):
    """Schema for productivity trends response"""
    period_days: int
    data_points: int
    trends: Dict[str, float]
    averages: Dict[str, float]
    best_performance: Dict[str, Any]
    improvement_indicators: Dict[str, Any]
    daily_data: List[Dict[str, Any]]


class ReadingSpeedAnalyticsResponse(BaseModel):
    """Schema for reading speed analytics response"""
    period_days: int
    session_count: int
    content_type: str
    speed_statistics: Dict[str, float]
    trend_analysis: Dict[str, Any]
    performance_patterns: Dict[str, Any]
    recommendations: List[str]


class BottleneckAnalysisResponse(BaseModel):
    """Schema for bottleneck analysis response"""
    analysis_period_days: int
    sessions_analyzed: int
    overall_health: str
    bottlenecks_found: int
    severity_breakdown: Dict[str, int]
    bottlenecks: List[Dict[str, Any]]
    summary: Dict[str, List[str]]
    action_plan: List[Dict[str, Any]]


class PerformanceMetricsResponse(BaseModel):
    """Schema for performance metrics response"""
    id: int
    date: datetime
    total_study_time_minutes: int
    total_active_time_minutes: int
    total_pages_covered: int
    session_count: int
    average_focus_score: float
    average_productivity_score: float
    average_reading_speed: float
    consistency_score: float
    productivity_trend: ProductivityTrend
    focus_trend: ProductivityTrend
    speed_trend: ProductivityTrend
    
    class Config:
        from_attributes = True