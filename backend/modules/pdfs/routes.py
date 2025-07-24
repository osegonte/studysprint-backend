"""
StudySprint 4.0 - PDF API Routes
REST API endpoints for PDF management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import mimetypes
from pathlib import Path

from database import get_db
from .schemas import (
    PDFUpload, ExercisePDFAttach, PDFResponse, PDFListResponse,
    PDFUploadResponse, PDFSearchResponse, HighlightCreate, HighlightResponse
)
from .services import pdf_service

router = APIRouter()


@router.post("/upload", response_model=PDFUploadResponse, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    topic_id: Optional[int] = Form(None),
    pdf_type: str = Form("study"),
    db: Session = Depends(get_db)
):
    """Upload PDF file with metadata extraction"""
    try:
        upload_data = PDFUpload(
            topic_id=topic_id,
            pdf_type=pdf_type
        )
        
        pdf = await pdf_service.upload_pdf(db, file, upload_data)
        
        return PDFUploadResponse(
            message=f"PDF '{file.filename}' uploaded successfully",
            pdf=PDFResponse.model_validate(pdf),
            processing_status=pdf.processing_status,
            estimated_processing_time=30 if pdf.processing_status == "pending" else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{study_pdf_id}/attach-exercise", response_model=PDFResponse)
async def attach_exercise_pdf(
    study_pdf_id: int,
    attach_data: ExercisePDFAttach,
    db: Session = Depends(get_db)
):
    """Attach exercise PDF to study PDF"""
    pdf = pdf_service.attach_exercise_pdf(db, study_pdf_id, attach_data)
    return PDFResponse.model_validate(pdf)


@router.get("/", response_model=PDFListResponse)
async def list_pdfs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    topic_id: Optional[int] = Query(None),
    pdf_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List PDFs with filtering"""
    pdfs, total = pdf_service.get_pdfs(
        db, skip=skip, limit=limit, topic_id=topic_id,
        pdf_type=pdf_type, search=search
    )
    
    # Enhance PDFs with additional info
    pdf_responses = []
    for pdf in pdfs:
        pdf_response = PDFResponse.model_validate(pdf)
        pdf_response.has_thumbnail = bool(pdf.thumbnail_path)
        pdf_response.exercise_pdfs_count = len(pdf.exercise_pdfs) if hasattr(pdf, 'exercise_pdfs') else 0
        pdf_responses.append(pdf_response)
    
    total_pages = (total + limit - 1) // limit
    
    return PDFListResponse(
        items=pdf_responses,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        total_pages=total_pages
    )


@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Get PDF details"""
    pdf = pdf_service.get_pdf_by_id(db, pdf_id)
    pdf_response = PDFResponse.model_validate(pdf)
    pdf_response.has_thumbnail = bool(pdf.thumbnail_path)
    pdf_response.exercise_pdfs_count = len(pdf.exercise_pdfs) if hasattr(pdf, 'exercise_pdfs') else 0
    return pdf_response


@router.get("/{pdf_id}/content")
async def get_pdf_content(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Serve PDF file with streaming support"""
    try:
        file_path = pdf_service.get_pdf_content_path(db, pdf_id)
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Get MIME type
        content_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
        
        return FileResponse(
            path=file_path,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={Path(file_path).name}",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {str(e)}")


@router.get("/{pdf_id}/thumbnail")
async def get_pdf_thumbnail(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Get PDF thumbnail"""
    try:
        thumbnail_path = pdf_service.get_pdf_thumbnail_path(db, pdf_id)
        
        if not thumbnail_path or not Path(thumbnail_path).exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            path=thumbnail_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=86400"  # 24 hours
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving thumbnail: {str(e)}")


@router.delete("/{pdf_id}")
async def delete_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Delete PDF and associated files"""
    success = pdf_service.delete_pdf(db, pdf_id)
    return {
        "success": success,
        "message": "PDF deleted successfully"
    }


@router.get("/search", response_model=List[PDFSearchResponse])
async def search_pdfs(
    q: str = Query(..., min_length=1, description="Search query"),
    topic_id: Optional[int] = Query(None),
    pdf_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search PDFs by content and metadata"""
    results = pdf_service.search_pdfs(
        db, query=q, topic_id=topic_id, pdf_type=pdf_type, limit=limit
    )
    
    return [PDFSearchResponse(**result) for result in results]


@router.post("/{pdf_id}/highlights", response_model=HighlightResponse)
async def create_highlight(
    pdf_id: int,
    highlight_data: HighlightCreate,
    db: Session = Depends(get_db)
):
    """Create PDF highlight"""
    highlight = pdf_service.create_highlight(db, pdf_id, highlight_data)
    return HighlightResponse.model_validate(highlight)


@router.get("/{pdf_id}/highlights/page/{page_number}", response_model=List[HighlightResponse])
async def get_page_highlights(
    pdf_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Get highlights for a specific page"""
    highlights = pdf_service.get_page_highlights(db, pdf_id, page_number)
    return [HighlightResponse.model_validate(h) for h in highlights]


@router.get("/{pdf_id}/highlights", response_model=List[HighlightResponse])
async def get_pdf_highlights(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Get all highlights for a PDF"""
    pdf = pdf_service.get_pdf_by_id(db, pdf_id)  # Verify PDF exists
    highlights = db.query(pdf_service.model).filter(
        pdf_service.model.pdf_id == pdf_id
    ).all()
    return [HighlightResponse.model_validate(h) for h in highlights]


@router.put("/{pdf_id}/highlights/{highlight_id}", response_model=HighlightResponse)
async def update_highlight(
    pdf_id: int,
    highlight_id: int,
    highlight_data: HighlightCreate,
    db: Session = Depends(get_db)
):
    """Update PDF highlight"""
    try:
        from .models import PDFHighlight
        
        # Get existing highlight
        highlight = db.query(PDFHighlight).filter(
            PDFHighlight.id == highlight_id,
            PDFHighlight.pdf_id == pdf_id
        ).first()
        
        if not highlight:
            raise HTTPException(status_code=404, detail="Highlight not found")
        
        # Update fields
        update_data = highlight_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(highlight, field, value)
        
        highlight.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(highlight)
        
        return HighlightResponse.model_validate(highlight)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating highlight: {str(e)}")


@router.delete("/{pdf_id}/highlights/{highlight_id}")
async def delete_highlight(
    pdf_id: int,
    highlight_id: int,
    db: Session = Depends(get_db)
):
    """Delete PDF highlight"""
    try:
        from .models import PDFHighlight
        
        highlight = db.query(PDFHighlight).filter(
            PDFHighlight.id == highlight_id,
            PDFHighlight.pdf_id == pdf_id
        ).first()
        
        if not highlight:
            raise HTTPException(status_code=404, detail="Highlight not found")
        
        db.delete(highlight)
        db.commit()
        
        return {"success": True, "message": "Highlight deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting highlight: {str(e)}")


@router.get("/{pdf_id}/metadata")
async def get_pdf_metadata(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed PDF metadata"""
    pdf = pdf_service.get_pdf_by_id(db, pdf_id)
    
    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "original_filename": pdf.original_filename,
        "file_size": pdf.file_size,
        "file_size_mb": pdf.file_size_mb,
        "page_count": pdf.page_count,
        "processing_status": pdf.processing_status,
        "processing_error": pdf.processing_error,
        "content_type": pdf.content_type,
        "file_hash": pdf.file_hash,
        "metadata": pdf.metadata,
        "total_study_time": pdf.total_study_time,
        "completion_percentage": pdf.completion_percentage,
        "last_accessed_at": pdf.last_accessed_at,
        "last_page_accessed": pdf.last_page_accessed,
        "created_at": pdf.created_at,
        "updated_at": pdf.updated_at,
        "has_thumbnail": bool(pdf.thumbnail_path),
        "topic_info": {
            "id": pdf.topic.id,
            "name": pdf.topic.name,
            "color": pdf.topic.color
        } if pdf.topic else None,
        "parent_pdf": {
            "id": pdf.parent_pdf.id,
            "filename": pdf.parent_pdf.filename
        } if pdf.parent_pdf else None,
        "exercise_pdfs": [
            {
                "id": exercise.id,
                "filename": exercise.filename,
                "page_count": exercise.page_count,
                "processing_status": exercise.processing_status
            }
            for exercise in getattr(pdf, 'exercise_pdfs', [])
        ],
        "highlight_count": len(getattr(pdf, 'highlights', [])),
        "statistics": {
            "pages_per_study_hour": (pdf.page_count / (pdf.total_study_time / 3600)) if pdf.total_study_time > 0 else 0,
            "average_time_per_page": (pdf.total_study_time / pdf.page_count) if pdf.page_count > 0 and pdf.total_study_time > 0 else 0
        }
    }


@router.patch("/{pdf_id}/progress")
async def update_pdf_progress(
    pdf_id: int,
    current_page: int = Query(..., ge=1, description="Current page number"),
    completion_percentage: Optional[float] = Query(None, ge=0, le=100, description="Completion percentage"),
    db: Session = Depends(get_db)
):
    """Update PDF reading progress"""
    try:
        pdf = pdf_service.get_pdf_by_id(db, pdf_id)
        
        # Validate current page
        if current_page > pdf.page_count:
            raise HTTPException(
                status_code=400, 
                detail=f"Page {current_page} exceeds PDF page count ({pdf.page_count})"
            )
        
        # Update progress
        pdf.last_page_accessed = current_page
        pdf.last_accessed_at = datetime.utcnow()
        
        # Calculate or use provided completion percentage
        if completion_percentage is not None:
            pdf.completion_percentage = completion_percentage
        else:
            # Auto-calculate based on current page
            pdf.completion_percentage = (current_page / pdf.page_count) * 100
        
        pdf.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pdf)
        
        return {
            "success": True,
            "message": f"Progress updated to page {current_page} ({pdf.completion_percentage:.1f}%)",
            "current_page": pdf.last_page_accessed,
            "completion_percentage": pdf.completion_percentage,
            "pages_remaining": pdf.page_count - current_page
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating progress: {str(e)}")


@router.get("/{pdf_id}/statistics")
async def get_pdf_statistics(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """Get PDF reading statistics"""
    pdf = pdf_service.get_pdf_by_id(db, pdf_id)
    
    # Get session statistics for this PDF
    from modules.sessions.models import Session as SessionModel
    sessions = db.query(SessionModel).filter(SessionModel.pdf_id == pdf_id).all()
    
    total_sessions = len(sessions)
    total_session_time = sum(s.total_duration_seconds for s in sessions)
    active_session_time = sum(s.active_duration_seconds for s in sessions)
    
    # Calculate averages
    avg_session_duration = total_session_time / total_sessions if total_sessions > 0 else 0
    avg_pages_per_session = sum(s.pages_covered for s in sessions) / total_sessions if total_sessions > 0 else 0
    avg_reading_speed = sum(s.reading_speed for s in sessions if s.reading_speed > 0) / max(1, len([s for s in sessions if s.reading_speed > 0]))
    
    return {
        "pdf_id": pdf_id,
        "filename": pdf.filename,
        "total_pages": pdf.page_count,
        "completion_percentage": pdf.completion_percentage,
        "last_page_accessed": pdf.last_page_accessed,
        "total_study_time": pdf.total_study_time,
        "session_statistics": {
            "total_sessions": total_sessions,
            "total_session_time": total_session_time,
            "active_session_time": active_session_time,
            "average_session_duration": avg_session_duration,
            "efficiency_percentage": (active_session_time / total_session_time * 100) if total_session_time > 0 else 0
        },
        "reading_statistics": {
            "average_pages_per_session": avg_pages_per_session,
            "average_reading_speed": avg_reading_speed,
            "estimated_completion_time": (pdf.page_count - pdf.last_page_accessed) / avg_reading_speed if avg_reading_speed > 0 else None,
            "pages_per_hour": (pdf.page_count / (pdf.total_study_time / 3600)) if pdf.total_study_time > 0 else 0
        },
        "engagement": {
            "highlight_count": len(getattr(pdf, 'highlights', [])),
            "last_accessed": pdf.last_accessed_at,
            "days_since_last_access": (datetime.utcnow() - pdf.last_accessed_at).days if pdf.last_accessed_at else None
        }
    }