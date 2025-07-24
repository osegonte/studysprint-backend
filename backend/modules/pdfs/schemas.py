"""
StudySprint 4.0 - PDF Schemas
Pydantic models for PDF API validation
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PDFType(str, Enum):
    STUDY = "study"
    EXERCISE = "exercise"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFUpload(BaseModel):
    """Schema for PDF upload"""
    topic_id: Optional[int] = Field(None, description="Topic ID to associate with")
    pdf_type: PDFType = Field(PDFType.STUDY, description="Type of PDF")
    
    @field_validator('topic_id')
    @classmethod
    def validate_topic_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Topic ID must be positive')
        return v


class ExercisePDFAttach(BaseModel):
    """Schema for attaching exercise PDF"""
    exercise_pdf_id: int = Field(..., description="ID of the exercise PDF to attach")
    
    @field_validator('exercise_pdf_id')
    @classmethod
    def validate_exercise_pdf_id(cls, v):
        if v <= 0:
            raise ValueError('Exercise PDF ID must be positive')
        return v


class PDFResponse(BaseModel):
    """Schema for PDF response"""
    id: int
    filename: str
    original_filename: str
    pdf_type: PDFType
    topic_id: Optional[int]
    parent_pdf_id: Optional[int]
    file_size: int
    file_size_mb: float
    content_type: str
    page_count: int
    processing_status: ProcessingStatus
    processing_error: Optional[str]
    total_study_time: int
    completion_percentage: float
    last_accessed_at: Optional[datetime]
    last_page_accessed: int
    pdf_metadata: Dict[str, Any]  # Changed from metadata to pdf_metadata
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    has_thumbnail: bool = False
    exercise_pdfs_count: int = 0
    
    class Config:
        from_attributes = True


class PDFListResponse(BaseModel):
    """Schema for paginated PDF list"""
    items: List[PDFResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PDFMetadata(BaseModel):
    """Schema for PDF metadata"""
    id: int
    filename: str
    file_size: int
    page_count: int
    processing_status: ProcessingStatus
    content_preview: Optional[str] = Field(None, max_length=500)
    pdf_metadata: Dict[str, Any]  # Changed from metadata to pdf_metadata


class PDFSearchResponse(BaseModel):
    """Schema for PDF search results"""
    id: int
    filename: str
    original_filename: str
    pdf_type: PDFType
    topic_id: Optional[int]
    relevance_score: float
    matched_content: Optional[str] = None
    page_matches: List[int] = []


class HighlightCreate(BaseModel):
    """Schema for creating PDF highlights"""
    page_number: int = Field(..., ge=1)
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    selected_text: Optional[str] = Field(None, max_length=1000)
    note: Optional[str] = Field(None, max_length=2000)
    color: str = Field("#FFFF00", pattern=r"^#[0-9A-Fa-f]{6}$")


class HighlightResponse(BaseModel):
    """Schema for highlight response"""
    id: int
    pdf_id: int
    page_number: int
    x: float
    y: float
    width: float
    height: float
    selected_text: Optional[str]
    note: Optional[str]
    color: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PDFUploadResponse(BaseModel):
    """Schema for PDF upload response"""
    success: bool = True
    message: str
    pdf: PDFResponse
    processing_status: ProcessingStatus
    estimated_processing_time: Optional[int] = None  # seconds