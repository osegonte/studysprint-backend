"""
StudySprint 4.0 - PDF Models
SQLAlchemy models for PDF management with exercise integration
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from pathlib import Path

from database import Base


class PDFType(str, Enum):
    """PDF type enumeration"""
    STUDY = "study"
    EXERCISE = "exercise"


class ProcessingStatus(str, Enum):
    """PDF processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDF(Base):
    """PDF model with metadata and relationships"""
    __tablename__ = "pdfs"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    
    # PDF type and relationships
    pdf_type = Column(String(20), default=PDFType.STUDY.value)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    parent_pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=True)  # For exercise PDFs
    
    # File metadata
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), default="application/pdf")
    page_count = Column(Integer, default=0)
    
    # Processing status
    processing_status = Column(String(20), default=ProcessingStatus.PENDING.value)
    processing_error = Column(Text, nullable=True)
    
    # Content and search
    text_content = Column(Text, nullable=True)  # Extracted text for search
    thumbnail_path = Column(String(500), nullable=True)
    
    # Study tracking
    total_study_time = Column(Integer, default=0)  # seconds
    completion_percentage = Column(Float, default=0.0)
    last_accessed_at = Column(DateTime, nullable=True)
    last_page_accessed = Column(Integer, default=1)
    
    # PDF metadata - renamed from 'metadata' to avoid SQLAlchemy conflict
    pdf_metadata = Column(JSON, default=dict)  # Additional PDF metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic", back_populates="pdfs")
    parent_pdf = relationship("PDF", remote_side=[id], backref="exercise_pdfs")
    sessions = relationship("Session", back_populates="pdf")
    
    def __repr__(self):
        return f"<PDF(id={self.id}, filename='{self.filename}', type={self.pdf_type})>"
    
    @property
    def is_exercise(self) -> bool:
        """Check if this is an exercise PDF"""
        return self.pdf_type == PDFType.EXERCISE.value
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)
    
    def update_access(self, page_number: int = None):
        """Update last access information"""
        self.last_accessed_at = datetime.utcnow()
        if page_number:
            self.last_page_accessed = page_number
        self.updated_at = datetime.utcnow()


class PDFHighlight(Base):
    """PDF highlight/annotation model"""
    __tablename__ = "pdf_highlights"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    
    # Highlight coordinates and dimensions
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Highlight content
    selected_text = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    color = Column(String(7), default="#FFFF00")  # Yellow by default
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pdf = relationship("PDF", backref="highlights")
    
    def __repr__(self):
        return f"<PDFHighlight(pdf_id={self.pdf_id}, page={self.page_number})>"


# Update existing models to add relationships
def update_existing_models():
    """Update existing models with PDF relationships"""
    # This will be imported in the main models to add relationships
    pass