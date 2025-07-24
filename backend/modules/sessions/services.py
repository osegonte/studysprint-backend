"""
StudySprint 4.0 - Sessions Service
Business logic for session management and real-time tracking
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from shared.database import DatabaseService
from shared.utils import TimeTracker, format_duration
from .models import Session as SessionModel, PageTime, SessionStatus, SessionType
from .schemas import SessionCreate, SessionUpdate, PageTimeCreate
from core.exceptions import NotFoundException, SessionException

logger = logging.getLogger(__name__)


class SessionsService(DatabaseService):
    """Service class for session management"""
    
    def __init__(self):
        super().__init__(SessionModel)
        self.active_timers: Dict[int, TimeTracker] = {}
    
    def start_session(self, db: Session, session_data: SessionCreate) -> SessionModel:
        """Start a new study session"""
        try:
            session = SessionModel(
                session_type=session_data.session_type.value,
                status=SessionStatus.ACTIVE.value,
                topic_id=session_data.topic_id,
                pdf_id=session_data.pdf_id,
                start_page=session_data.start_page,
                current_page=session_data.start_page,
                session_goal=session_data.session_goal,
                start_time=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Initialize timer
            timer = TimeTracker()
            timer.start()
            self.active_timers[session.id] = timer
            
            logger.info(f"✅ Started session {session.id} ({session.session_type})")
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to start session: {e}")
            raise
    
    def pause_session(self, db: Session, session_id: int) -> SessionModel:
        """Pause an active session"""
        try:
            session = self.get_session_by_id(db, session_id)
            
            if session.status != SessionStatus.ACTIVE.value:
                raise SessionException("Only active sessions can be paused")
            
            # Update session
            session.status = SessionStatus.PAUSED.value
            session.pause_time = datetime.utcnow()
            
            # Pause timer
            if session_id in self.active_timers:
                timer = self.active_timers[session_id]
                timer.pause()
                session.active_duration_seconds = timer.get_current_total()
            
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
            
            logger.info(f"⏸️ Paused session {session_id}")
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to pause session {session_id}: {e}")
            raise
    
    def resume_session(self, db: Session, session_id: int) -> SessionModel:
        """Resume a paused session"""
        try:
            session = self.get_session_by_id(db, session_id)
            
            if session.status != SessionStatus.PAUSED.value:
                raise SessionException("Only paused sessions can be resumed")
            
            # Update session
            session.status = SessionStatus.ACTIVE.value
            session.pause_time = None
            
            # Resume timer
            if session_id in self.active_timers:
                timer = self.active_timers[session_id]
                timer.resume()
            else:
                # Create new timer if not exists
                timer = TimeTracker()
                timer.total_seconds = session.active_duration_seconds
                timer.start()
                self.active_timers[session_id] = timer
            
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
            
            logger.info(f"▶️ Resumed session {session_id}")
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to resume session {session_id}: {e}")
            raise
    
    def end_session(self, db: Session, session_id: int) -> SessionModel:
        """End a session and calculate final metrics"""
        try:
            session = self.get_session_by_id(db, session_id)
            
            if session.status in [SessionStatus.COMPLETED.value, SessionStatus.CANCELLED.value]:
                raise SessionException("Session is already ended")
            
            # Calculate final durations
            if session_id in self.active_timers:
                timer = self.active_timers[session_id]
                timer.stop()
                session.active_duration_seconds = timer.total_seconds
                del self.active_timers[session_id]
            
            # Calculate total duration
            if session.start_time:
                total_elapsed = datetime.utcnow() - session.start_time
                session.total_duration_seconds = int(total_elapsed.total_seconds())
                session.break_duration_seconds = session.total_duration_seconds - session.active_duration_seconds
            
            # Calculate pages covered
            if session.end_page:
                session.pages_covered = max(0, session.end_page - session.start_page + 1)
            
            # Update status and end time
            session.status = SessionStatus.COMPLETED.value
            session.end_time = datetime.utcnow()
            
            # Calculate metrics
            session.calculate_metrics()
            
            db.commit()
            db.refresh(session)
            
            logger.info(f"✅ Ended session {session_id} - Duration: {format_duration(session.total_duration_seconds)}")
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to end session {session_id}: {e}")
            raise
    
    def get_session_by_id(self, db: Session, session_id: int) -> SessionModel:
        """Get session by ID"""
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise NotFoundException("Session", session_id)
        return session
    
    def get_sessions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        topic_id: Optional[int] = None,
        session_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> tuple[List[SessionModel], int]:
        """Get sessions with filtering"""
        query = db.query(SessionModel)
        
        if topic_id:
            query = query.filter(SessionModel.topic_id == topic_id)
        if session_type:
            query = query.filter(SessionModel.session_type == session_type)
        if status:
            query = query.filter(SessionModel.status == status)
        
        total = query.count()
        sessions = query.order_by(SessionModel.start_time.desc()).offset(skip).limit(limit).all()
        
        return sessions, total
    
    def log_page_time(self, db: Session, session_id: int, page_data: PageTimeCreate) -> PageTime:
        """Log page timing data"""
        try:
            session = self.get_session_by_id(db, session_id)
            
            # Check if page was already logged
            existing = db.query(PageTime).filter(
                PageTime.session_id == session_id,
                PageTime.page_number == page_data.page_number
            ).first()
            
            if existing:
                existing.revisited = True
                existing.duration_seconds += page_data.duration_seconds
                page_time = existing
            else:
                page_time = PageTime(
                    session_id=session_id,
                    page_number=page_data.page_number,
                    start_time=datetime.utcnow(),
                    duration_seconds=page_data.duration_seconds,
                    reading_speed=page_data.reading_speed or 0.0
                )
                db.add(page_time)
            
            # Update session current page
            session.current_page = page_data.page_number
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(page_time)
            
            return page_time
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to log page time: {e}")
            raise
    
    def get_current_timer_state(self, session_id: int) -> Dict[str, Any]:
        """Get current timer state for WebSocket updates"""
        if session_id in self.active_timers:
            timer = self.active_timers[session_id]
            return {
                "session_id": session_id,
                "elapsed_seconds": timer.get_current_total(),
                "is_running": timer.is_running,
                "current_time": datetime.utcnow()
            }
        return {"session_id": session_id, "elapsed_seconds": 0, "is_running": False}


# Global service instance
sessions_service = SessionsService()