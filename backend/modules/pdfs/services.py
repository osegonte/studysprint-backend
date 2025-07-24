"""
StudySprint 4.0 - PDF Services
Business logic for PDF management and processing
"""
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import logging
import PyPDF2
from PIL import Image
import io
import os
import shutil

from shared.database import DatabaseService
from shared.utils import generate_uuid, safe_filename, validate_file_type
from core.config import settings
from core.exceptions import NotFoundException, ValidationException, FileUploadException
from .models import PDF, PDFHighlight, PDFType, ProcessingStatus
from .schemas import PDFUpload, ExercisePDFAttach, HighlightCreate

logger = logging.getLogger(__name__)


class PDFService(DatabaseService):
    """Service class for PDF management"""
    
    def __init__(self):
        super().__init__(PDF)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIR)
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_pdf(
        self,
        db: Session,
        file: UploadFile,
        upload_data: PDFUpload
    ) -> PDF:
        """Upload and process PDF file"""
        try:
            # Validate file
            if not file.filename:
                raise FileUploadException("No filename provided")
            
            if not validate_file_type(file.filename, ["pdf"]):
                raise FileUploadException("Only PDF files are allowed")
            
            # Read file content
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                raise FileUploadException(f"File size exceeds {settings.MAX_FILE_SIZE} bytes")
            
            # Generate file hash for deduplication
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Check for duplicate
            existing_pdf = db.query(PDF).filter(PDF.file_hash == file_hash).first()
            if existing_pdf:
                logger.info(f"PDF already exists with hash {file_hash}")
                return existing_pdf
            
            # Generate safe filename
            safe_name = safe_filename(file.filename)
            file_path = self.upload_dir / safe_name
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Create PDF record
            pdf = PDF(
                filename=safe_name,
                original_filename=file.filename,
                file_path=str(file_path),
                file_hash=file_hash,
                pdf_type=upload_data.pdf_type.value,
                topic_id=upload_data.topic_id,
                file_size=len(content),
                content_type=file.content_type or "application/pdf",
                processing_status=ProcessingStatus.PENDING.value
            )
            
            db.add(pdf)
            db.commit()
            db.refresh(pdf)
            
            # Process PDF asynchronously
            await self._process_pdf(db, pdf, content)
            
            logger.info(f"✅ Uploaded PDF: {file.filename} -> {safe_name}")
            return pdf
            
        except Exception as e:
            logger.error(f"❌ Failed to upload PDF: {e}")
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise
    
    async def _process_pdf(self, db: Session, pdf: PDF, content: bytes):
        """Process PDF for metadata extraction"""
        try:
            pdf.processing_status = ProcessingStatus.PROCESSING.value
            db.commit()
            
            # Extract metadata using PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            
            # Get page count
            pdf.page_count = len(pdf_reader.pages)
            
            # Extract text content for search
            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                text_content.append(text)
            
            pdf.text_content = "\n".join(text_content)
            
            # Extract metadata - use pdf_metadata instead of metadata
            pdf_meta = {}
            if pdf_reader.metadata:
                pdf_meta.update({
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                    "modification_date": str(pdf_reader.metadata.get("/ModDate", ""))
                })
            
            pdf.pdf_metadata = pdf_meta  # Use pdf_metadata field
            
            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(pdf, content)
            if thumbnail_path:
                pdf.thumbnail_path = str(thumbnail_path)
            
            pdf.processing_status = ProcessingStatus.COMPLETED.value
            pdf.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Processed PDF {pdf.filename}: {pdf.page_count} pages")
            
        except Exception as e:
            pdf.processing_status = ProcessingStatus.FAILED.value
            pdf.processing_error = str(e)
            db.commit()
            logger.error(f"❌ Failed to process PDF {pdf.filename}: {e}")
    
    async def _generate_thumbnail(self, pdf: PDF, content: bytes) -> Optional[Path]:
        """Generate thumbnail for PDF first page"""
        try:
            # This is a simplified thumbnail generation
            # In production, you might want to use pdf2image or similar
            thumbnail_name = f"{Path(pdf.filename).stem}_thumb.jpg"
            thumbnail_path = self.thumbnail_dir / thumbnail_name
            
            # For now, create a placeholder thumbnail
            # In real implementation, use pdf2image or similar library
            placeholder_image = Image.new('RGB', (200, 300), color='lightgray')
            placeholder_image.save(thumbnail_path, 'JPEG')
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"❌ Failed to generate thumbnail for {pdf.filename}: {e}")
            return None
    
    def attach_exercise_pdf(
        self,
        db: Session,
        study_pdf_id: int,
        attach_data: ExercisePDFAttach
    ) -> PDF:
        """Attach exercise PDF to study PDF"""
        try:
            # Get study PDF
            study_pdf = self.get_pdf_by_id(db, study_pdf_id)
            if study_pdf.pdf_type != PDFType.STUDY.value:
                raise ValidationException("Can only attach exercises to study PDFs")
            
            # Get exercise PDF
            exercise_pdf = self.get_pdf_by_id(db, attach_data.exercise_pdf_id)
            if exercise_pdf.pdf_type != PDFType.EXERCISE.value:
                raise ValidationException("Can only attach exercise type PDFs")
            
            # Check if already attached
            if exercise_pdf.parent_pdf_id == study_pdf_id:
                raise ValidationException("Exercise PDF is already attached to this study PDF")
            
            # Attach exercise
            exercise_pdf.parent_pdf_id = study_pdf_id
            exercise_pdf.topic_id = study_pdf.topic_id  # Inherit topic
            exercise_pdf.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(exercise_pdf)
            
            logger.info(f"✅ Attached exercise PDF {exercise_pdf.filename} to {study_pdf.filename}")
            return exercise_pdf
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to attach exercise PDF: {e}")
            raise
    
    def get_pdfs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        topic_id: Optional[int] = None,
        pdf_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[PDF], int]:
        """Get PDFs with filtering"""
        query = db.query(PDF)
        
        # Apply filters
        if topic_id:
            query = query.filter(PDF.topic_id == topic_id)
        
        if pdf_type:
            query = query.filter(PDF.pdf_type == pdf_type)
        
        if search:
            query = query.filter(
                PDF.filename.ilike(f"%{search}%") |
                PDF.original_filename.ilike(f"%{search}%") |
                PDF.text_content.ilike(f"%{search}%")
            )
        
        total = query.count()
        pdfs = query.order_by(PDF.updated_at.desc()).offset(skip).limit(limit).all()
        
        return pdfs, total
    
    def get_pdf_by_id(self, db: Session, pdf_id: int) -> PDF:
        """Get PDF by ID"""
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        if not pdf:
            raise NotFoundException("PDF", pdf_id)
        return pdf
    
    def get_pdf_content_path(self, db: Session, pdf_id: int) -> str:
        """Get PDF file path for serving"""
        pdf = self.get_pdf_by_id(db, pdf_id)
        
        # Update access information
        pdf.update_access()
        db.commit()
        
        return pdf.file_path
    
    def get_pdf_thumbnail_path(self, db: Session, pdf_id: int) -> Optional[str]:
        """Get PDF thumbnail path"""
        pdf = self.get_pdf_by_id(db, pdf_id)
        return pdf.thumbnail_path
    
    def delete_pdf(self, db: Session, pdf_id: int) -> bool:
        """Delete PDF and associated files"""
        try:
            pdf = self.get_pdf_by_id(db, pdf_id)
            
            # Delete associated files
            file_path = Path(pdf.file_path)
            if file_path.exists():
                file_path.unlink()
            
            if pdf.thumbnail_path:
                thumbnail_path = Path(pdf.thumbnail_path)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
            
            # Delete database record
            db.delete(pdf)
            db.commit()
            
            logger.info(f"✅ Deleted PDF: {pdf.filename}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to delete PDF {pdf_id}: {e}")
            raise
    
    def search_pdfs(
        self,
        db: Session,
        query: str,
        topic_id: Optional[int] = None,
        pdf_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Advanced PDF search"""
        search_query = db.query(PDF)
        
        # Apply filters
        if topic_id:
            search_query = search_query.filter(PDF.topic_id == topic_id)
        
        if pdf_type:
            search_query = search_query.filter(PDF.pdf_type == pdf_type)
        
        # Search in filename and content
        search_query = search_query.filter(
            PDF.filename.ilike(f"%{query}%") |
            PDF.original_filename.ilike(f"%{query}%") |
            PDF.text_content.ilike(f"%{query}%")
        )
        
        pdfs = search_query.limit(limit).all()
        
        # Calculate relevance scores (simplified)
        results = []
        for pdf in pdfs:
            score = 0.0
            
            # Filename match gets high score
            if query.lower() in pdf.filename.lower():
                score += 1.0
            
            # Content match gets lower score
            if pdf.text_content and query.lower() in pdf.text_content.lower():
                score += 0.5
            
            results.append({
                "id": pdf.id,
                "filename": pdf.filename,
                "original_filename": pdf.original_filename,
                "pdf_type": pdf.pdf_type,
                "topic_id": pdf.topic_id,
                "relevance_score": score,
                "matched_content": self._extract_matched_content(pdf.text_content, query)
            })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    def _extract_matched_content(self, content: str, query: str, context_length: int = 200) -> Optional[str]:
        """Extract content snippet around matched query"""
        if not content or not query:
            return None
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        match_index = content_lower.find(query_lower)
        if match_index == -1:
            return None
        
        # Extract context around match
        start = max(0, match_index - context_length // 2)
        end = min(len(content), match_index + len(query) + context_length // 2)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def create_highlight(
        self,
        db: Session,
        pdf_id: int,
        highlight_data: HighlightCreate
    ) -> PDFHighlight:
        """Create PDF highlight"""
        try:
            # Verify PDF exists
            pdf = self.get_pdf_by_id(db, pdf_id)
            
            # Validate page number
            if highlight_data.page_number > pdf.page_count:
                raise ValidationException(f"Page {highlight_data.page_number} does not exist in PDF")
            
            highlight = PDFHighlight(
                pdf_id=pdf_id,
                page_number=highlight_data.page_number,
                x=highlight_data.x,
                y=highlight_data.y,
                width=highlight_data.width,
                height=highlight_data.height,
                selected_text=highlight_data.selected_text,
                note=highlight_data.note,
                color=highlight_data.color
            )
            
            db.add(highlight)
            db.commit()
            db.refresh(highlight)
            
            logger.info(f"✅ Created highlight for PDF {pdf_id}, page {highlight_data.page_number}")
            return highlight
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create highlight: {e}")
            raise
    
    def get_page_highlights(
        self,
        db: Session,
        pdf_id: int,
        page_number: int
    ) -> List[PDFHighlight]:
        """Get highlights for a specific page"""
        return db.query(PDFHighlight).filter(
            PDFHighlight.pdf_id == pdf_id,
            PDFHighlight.page_number == page_number
        ).all()


# Global service instance
pdf_service = PDFService()