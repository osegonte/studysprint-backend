# backend/modules/analytics/routes.py
"""
StudySprint 4.0 - Analytics API Routes
REST API endpoints for advanced analytics and insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from .schemas import (
    SessionAnalyticsResponse, FocusAnalysisResponse, ProductivityTrendsResponse,
    ReadingSpeedAnalyticsResponse, BottleneckAnalysisResponse
)
from .services import analytics_service

router = APIRouter()


@router.get("/reading-speed", response_model=ReadingSpeedAnalyticsResponse)
async def get_reading_speed_analytics(
    content_type: Optional[str] = Query(None, description="Filter by content type (pdf, topic)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get reading speed analytics and trends"""
    analytics = analytics_service.get_reading_speed_analytics(db, content_type, days)
    return ReadingSpeedAnalyticsResponse(**analytics)


@router.get("/performance-trends", response_model=ProductivityTrendsResponse)
async def get_performance_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    trends = analytics_service.get_productivity_trends(db, days)
    return ProductivityTrendsResponse(**trends)


@router.get("/learning-velocity")
async def get_learning_velocity(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get learning progress rate analysis"""
    try:
        from modules.sessions.models import Session as SessionModel
        from modules.topics.models import Topic
        
        # Get completed sessions in the period
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        sessions = db.query(SessionModel).filter(
            SessionModel.start_time >= start_date,
            SessionModel.status == "completed"
        ).all()
        
        if not sessions:
            return {"message": f"No session data available for velocity analysis"}
        
        # Calculate velocity metrics
        total_pages = sum(s.pages_covered for s in sessions)
        total_time_hours = sum(s.active_duration_seconds for s in sessions) / 3600
        
        pages_per_day = total_pages / days
        pages_per_hour = total_pages / total_time_hours if total_time_hours > 0 else 0
        
        # Velocity trend
        daily_pages = {}
        for session in sessions:
            date_key = session.start_time.date()
            if date_key not in daily_pages:
                daily_pages[date_key] = 0
            daily_pages[date_key] += session.pages_covered
        
        daily_values = list(daily_pages.values())
        velocity_trend = analytics_service._calculate_trend(daily_values) if len(daily_values) > 1 else 0
        
        # Completion forecasting
        active_topics = db.query(Topic).filter(
            Topic.is_active == True,
            Topic.is_archived == False
        ).all()
        
        remaining_pages = sum(
            max(0, topic.total_pages - topic.completed_pages) 
            for topic in active_topics
        )
        
        estimated_days_to_complete = remaining_pages / pages_per_day if pages_per_day > 0 else None
        
        return {
            "analysis_period_days": days,
            "total_pages_covered": total_pages,
            "total_study_hours": total_time_hours,
            "velocity_metrics": {
                "pages_per_day": pages_per_day,
                "pages_per_hour": pages_per_hour,
                "sessions_per_day": len(sessions) / days
            },
            "velocity_trend": {
                "direction": "improving" if velocity_trend > 0.1 else "declining" if velocity_trend < -0.1 else "stable",
                "trend_value": velocity_trend
            },
            "forecasting": {
                "remaining_pages": remaining_pages,
                "estimated_days_to_complete": estimated_days_to_complete,
                "estimated_completion_date": (datetime.utcnow() + timedelta(days=estimated_days_to_complete)).isoformat() if estimated_days_to_complete else None
            },
            "recommendations": [
                f"Maintain current pace of {pages_per_day:.1f} pages/day" if velocity_trend >= 0 else "Consider increasing daily study time",
                f"Focus on {pages_per_hour:.1f} pages/hour efficiency" if pages_per_hour > 0 else "Track reading speed more consistently"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate learning velocity: {str(e)}")


@router.get("/bottlenecks", response_model=BottleneckAnalysisResponse)
async def identify_learning_bottlenecks(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Identify learning bottlenecks and performance issues"""
    bottlenecks = analytics_service.identify_learning_bottlenecks(db, days)
    return BottleneckAnalysisResponse(**bottlenecks)


@router.get("/sessions/{session_id}/analytics", response_model=SessionAnalyticsResponse)
async def get_session_analytics(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for a specific session"""
    analysis = analytics_service.analyze_session(db, session_id)
    return SessionAnalyticsResponse.model_validate(analysis["analytics"])


@router.get("/sessions/{session_id}/focus-analysis", response_model=FocusAnalysisResponse)
async def get_session_focus_analysis(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed focus analysis for a session"""
    focus_analysis = analytics_service.analyze_focus_patterns(db, session_id)
    return FocusAnalysisResponse(**focus_analysis)


@router.post("/sessions/{session_id}/page-analytics")
async def update_page_analytics(
    session_id: int,
    page_number: int = Query(..., ge=1, description="Page number"),
    time_spent_seconds: int = Query(..., ge=0, description="Time spent on page"),
    difficulty_rating: Optional[float] = Query(None, ge=0, le=1, description="User perceived difficulty"),
    db: Session = Depends(get_db)
):
    """Update page-level analytics"""
    try:
        from .models import PageAnalytics, SessionAnalytics
        
        # Get or create session analytics
        session_analytics = db.query(SessionAnalytics).filter(
            SessionAnalytics.session_id == session_id
        ).first()
        
        if not session_analytics:
            # Create session analytics first
            analytics_service.analyze_session(db, session_id)
            session_analytics = db.query(SessionAnalytics).filter(
                SessionAnalytics.session_id == session_id
            ).first()
        
        # Get or create page analytics
        page_analytics = db.query(PageAnalytics).filter(
            PageAnalytics.session_id == session_id,
            PageAnalytics.page_number == page_number
        ).first()
        
        if not page_analytics:
            page_analytics = PageAnalytics(
                session_id=session_id,
                session_analytics_id=session_analytics.id,
                page_number=page_number
            )
            db.add(page_analytics)
        
        # Update page analytics
        page_analytics.time_spent_seconds = time_spent_seconds
        page_analytics.effective_reading_time = int(time_spent_seconds * 0.8)  # Assume 80% effective
        
        if difficulty_rating is not None:
            page_analytics.user_perceived_difficulty = difficulty_rating
        
        # Calculate reading efficiency (simplified)
        optimal_time = 60  # 60 seconds per page target
        page_analytics.optimal_time_seconds = optimal_time
        page_analytics.reading_efficiency = min(1.0, optimal_time / max(1, time_spent_seconds))
        
        # Update engagement score
        page_analytics.calculate_engagement_score()
        
        db.commit()
        db.refresh(page_analytics)
        
        return {
            "success": True,
            "message": f"Updated analytics for page {page_number}",
            "page_analytics": {
                "page_number": page_analytics.page_number,
                "reading_efficiency": page_analytics.reading_efficiency,
                "engagement_score": page_analytics.engagement_score,
                "time_spent_seconds": page_analytics.time_spent_seconds,
                "difficulty_score": page_analytics.user_perceived_difficulty
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update page analytics: {str(e)}")


@router.get("/optimization-suggestions")
async def get_optimization_suggestions(
    session_id: Optional[int] = Query(None, description="Specific session to analyze"),
    days: int = Query(7, ge=1, le=30, description="Days of data to analyze for general suggestions"),
    db: Session = Depends(get_db)
):
    """Get personalized optimization suggestions"""
    try:
        suggestions = []
        
        if session_id:
            # Session-specific suggestions
            session_analysis = analytics_service.analyze_session(db, session_id)
            suggestions.extend(session_analysis["suggestions"])
        else:
            # General suggestions based on recent performance
            bottlenecks = analytics_service.identify_learning_bottlenecks(db, days)
            
            # Extract recommendations from bottlenecks
            for bottleneck in bottlenecks.get("bottlenecks", []):
                suggestions.extend(bottleneck.get("recommendations", [])[:2])  # Top 2 per bottleneck
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        return {
            "suggestions": unique_suggestions[:10],  # Top 10 suggestions
            "generated_at": datetime.utcnow().isoformat(),
            "based_on": "session_analysis" if session_id else f"last_{days}_days_performance"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization suggestions: {str(e)}")