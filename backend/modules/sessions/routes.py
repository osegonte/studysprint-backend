"""
StudySprint 4.0 - Sessions API Routes
REST API endpoints for session management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from .schemas import (
    SessionCreate, SessionUpdate, SessionResponse, SessionSummary,
    PageTimeCreate, PageTimeResponse, SessionAnalytics
)
from .services import sessions_service
from shared.utils import format_duration

router = APIRouter()


@router.post("/start", response_model=SessionResponse, status_code=201)
async def start_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """Start a new study session"""
    session = sessions_service.start_session(db, session_data)
    return session


@router.put("/{session_id}/pause", response_model=SessionResponse)
async def pause_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Pause an active session"""
    session = sessions_service.pause_session(db, session_id)
    return session


@router.put("/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Resume a paused session"""
    session = sessions_service.resume_session(db, session_id)
    return session


@router.put("/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: int,
    end_page: Optional[int] = Query(None, description="Final page number"),
    notes: Optional[str] = Query(None, description="Session notes"),
    db: Session = Depends(get_db)
):
    """End a session with summary"""
    session = sessions_service.get_session_by_id(db, session_id)
    
    # Update end page and notes if provided
    if end_page:
        session.end_page = end_page
    if notes:
        session.notes = notes
    
    session = sessions_service.end_session(db, session_id)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get session details"""
    session = sessions_service.get_session_by_id(db, session_id)
    return session


@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    topic_id: Optional[int] = Query(None),
    session_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get sessions with filtering"""
    sessions, total = sessions_service.get_sessions(
        db, skip=skip, limit=limit, topic_id=topic_id,
        session_type=session_type, status=status
    )
    return sessions


@router.post("/{session_id}/page-time", response_model=PageTimeResponse)
async def log_page_time(
    session_id: int,
    page_data: PageTimeCreate,
    db: Session = Depends(get_db)
):
    """Log page reading time"""
    page_time = sessions_service.log_page_time(db, session_id, page_data)
    return page_time


@router.get("/{session_id}/timer")
async def get_timer_state(session_id: int):
    """Get current timer state"""
    timer_state = sessions_service.get_current_timer_state(session_id)
    return timer_state


@router.get("/{session_id}/summary")
async def get_session_summary(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get session summary"""
    session = sessions_service.get_session_by_id(db, session_id)
    
    return {
        "id": session.id,
        "session_type": session.session_type,
        "status": session.status,
        "duration_formatted": format_duration(session.total_duration_seconds),
        "active_duration_formatted": format_duration(session.active_duration_seconds),
        "pages_covered": session.pages_covered,
        "reading_speed": session.reading_speed,
        "productivity_score": session.productivity_score,
        "focus_score": session.focus_score,
        "start_time": session.start_time,
        "end_time": session.end_time
    }