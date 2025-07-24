"""
StudySprint 4.0 - Topic Schemas
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from shared.types import Priority


class TopicBase(BaseModel):
    """Base topic schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Topic name")
    description: Optional[str] = Field(None, max_length=1000, description="Topic description")
    color: str = Field("#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    priority: str = Field("medium", description="Priority level")
    estimated_hours: Optional[float] = Field(0.0, ge=0, description="Estimated study hours")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ["low", "medium", "high", "urgent"]:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v


class TopicCreate(TopicBase):
    """Schema for creating a topic"""
    pass


class TopicUpdate(BaseModel):
    """Schema for updating a topic"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    priority: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ["low", "medium", "high", "urgent"]:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v


class TopicResponse(TopicBase):
    """Schema for topic response"""
    id: int
    total_pages: int
    completed_pages: int
    actual_hours: float
    completion_percentage: float
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_studied_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TopicProgress(BaseModel):
    """Schema for topic progress analytics"""
    id: int
    name: str
    total_pages: int
    completed_pages: int
    completion_percentage: float
    estimated_hours: float
    actual_hours: float
    pages_per_hour: float
    estimated_completion_date: Optional[datetime]
    study_streak_days: int
    last_studied_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """Schema for paginated topic list"""
    items: list[TopicResponse]
    total: int
    page: int
    size: int
    total_pages: int