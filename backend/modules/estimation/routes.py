# backend/modules/estimation/routes.py
"""
StudySprint 4.0 - Estimation API Routes
REST API endpoints for multi-level time estimation system
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from .schemas import (
    EstimationResponse, PDFEstimationResponse, TopicEstimationResponse,
    AppTotalEstimationResponse, EstimationAccuracyResponse, SessionEstimationUpdate
)
from .services import estimation_service

router = APIRouter()


@router.get("/pdf/{pdf_id}", response_model=PDFEstimationResponse)
async def get_pdf_estimation(
    pdf_id: int,
    difficulty: Optional[str] = Query("intermediate", description="Content difficulty level"),
    energy_level: Optional[float] = Query(0.8, ge=0, le=1, description="User energy level"),
    db: Session = Depends(get_db)
):
    """Get PDF completion time estimate with context factors"""
    user_context = {
        "difficulty": difficulty,
        "energy_level": energy_level
    }
    
    estimation = estimation_service.estimate_pdf_completion_time(db, pdf_id, user_context)
    return PDFEstimationResponse(**estimation)


@router.get("/topic/{topic_id}", response_model=TopicEstimationResponse)
async def get_topic_estimation(
    topic_id: int,
    difficulty: Optional[str] = Query("intermediate", description="Content difficulty level"),
    energy_level: Optional[float] = Query(0.8, ge=0, le=1, description="User energy level"),
    db: Session = Depends(get_db)
):
    """Get topic completion time estimate aggregated across PDFs"""
    user_context = {
        "difficulty": difficulty,
        "energy_level": energy_level
    }
    
    estimation = estimation_service.estimate_topic_completion_time(db, topic_id, user_context)
    return TopicEstimationResponse(**estimation)


@router.get("/app-total", response_model=AppTotalEstimationResponse)
async def get_app_total_estimation(
    difficulty: Optional[str] = Query("intermediate", description="Overall difficulty level"),
    energy_level: Optional[float] = Query(0.8, ge=0, le=1, description="User energy level"),
    db: Session = Depends(get_db)
):
    """Get total remaining work estimate across all active content"""
    user_context = {
        "difficulty": difficulty,
        "energy_level": energy_level
    }
    
    estimation = estimation_service.estimate_app_total_time(db, user_context)
    return AppTotalEstimationResponse(**estimation)


@router.post("/update-from-session", response_model=SessionEstimationUpdate)
async def update_estimations_from_session(
    session_id: int = Query(..., description="Completed session ID"),
    db: Session = Depends(get_db)
):
    """Update estimations based on actual session performance for learning"""
    try:
        update_result = estimation_service.update_estimation_from_session(db, session_id)
        return SessionEstimationUpdate(**update_result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update estimations: {str(e)}")


@router.get("/accuracy", response_model=EstimationAccuracyResponse)
async def get_estimation_accuracy(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get estimation accuracy analytics over time"""
    accuracy_data = estimation_service.get_estimation_accuracy(db)
    return EstimationAccuracyResponse(**accuracy_data)


@router.post("/recalculate")
async def recalculate_all_estimations(
    force: bool = Query(False, description="Force recalculation even for recent estimates"),
    db: Session = Depends(get_db)
):
    """Trigger recalculation of all estimations based on updated patterns"""
    try:
        from modules.topics.models import Topic
        from modules.pdfs.models import PDF
        
        recalculated = []
        
        # Recalculate all PDF estimations
        pdfs = db.query(PDF).filter(PDF.processing_status == "completed").all()
        for pdf in pdfs:
            try:
                estimation = estimation_service.estimate_pdf_completion_time(db, pdf.id)
                recalculated.append({
                    "type": "pdf",
                    "id": pdf.id,
                    "filename": pdf.filename,
                    "estimated_time_minutes": estimation["estimated_time_minutes"],
                    "confidence_level": estimation["confidence_level"]
                })
            except Exception as e:
                continue
        
        # Recalculate all topic estimations
        topics = db.query(Topic).filter(
            Topic.is_active == True,
            Topic.is_archived == False
        ).all()
        
        for topic in topics:
            try:
                estimation = estimation_service.estimate_topic_completion_time(db, topic.id)
                recalculated.append({
                    "type": "topic",
                    "id": topic.id,
                    "name": topic.name,
                    "estimated_time_minutes": estimation["estimated_time_minutes"],
                    "confidence_level": estimation["confidence_level"]
                })
            except Exception as e:
                continue
        
        return {
            "success": True,
            "message": f"Recalculated {len(recalculated)} estimations",
            "recalculated_count": len(recalculated),
            "estimations": recalculated,
            "recalculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate estimations: {str(e)}")


@router.get("/exercise/{exercise_id}")
async def get_exercise_estimation(
    exercise_id: int,
    difficulty: Optional[str] = Query("intermediate", description="Exercise difficulty level"),
    energy_level: Optional[float] = Query(0.8, ge=0, le=1, description="User energy level"),
    db: Session = Depends(get_db)
):
    """Get exercise PDF completion time estimate"""
    try:
        from modules.pdfs.models import PDF, PDFType
        
        exercise = db.query(PDF).filter(
            PDF.id == exercise_id,
            PDF.pdf_type == PDFType.EXERCISE.value
        ).first()
        
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise PDF not found")
        
        user_context = {
            "difficulty": difficulty,
            "energy_level": energy_level,
            "content_type": "exercise"  # Exercise context
        }
        
        estimation = estimation_service.estimate_pdf_completion_time(db, exercise_id, user_context)
        
        # Add exercise-specific context
        estimation["exercise_context"] = {
            "parent_pdf_id": exercise.parent_pdf_id,
            "is_practice": True,
            "difficulty_multiplier": 1.2  # Exercises typically take longer
        }
        
        return estimation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to estimate exercise time: {str(e)}")


@router.get("/user-patterns")
async def get_user_reading_patterns(
    content_type: Optional[str] = Query("pdf", description="Content type to analyze"),
    db: Session = Depends(get_db)
):
    """Get user reading patterns and performance data"""
    try:
        from .models import UserReadingPatterns, ContentType
        
        content_type_enum = ContentType.PDF if content_type == "pdf" else ContentType.PDF
        patterns = estimation_service._get_user_reading_patterns(db, content_type_enum)
        
        return {
            "content_type": content_type,
            "reading_patterns": {
                "average_speed_pages_per_minute": patterns.average_speed_pages_per_minute,
                "peak_speed_pages_per_minute": patterns.peak_speed_pages_per_minute,
                "minimum_speed_pages_per_minute": patterns.minimum_speed_pages_per_minute,
                "consistency_score": patterns.consistency_score,
                "improvement_trend": patterns.improvement_trend,
                "total_study_sessions": patterns.total_study_sessions
            },
            "time_of_day_performance": {
                "morning_factor": patterns.morning_performance_factor,
                "afternoon_factor": patterns.afternoon_performance_factor,
                "evening_factor": patterns.evening_performance_factor,
                "night_factor": patterns.night_performance_factor
            },
            "difficulty_adjustments": {
                "beginner": patterns.beginner_adjustment,
                "intermediate": patterns.intermediate_adjustment,
                "advanced": patterns.advanced_adjustment,
                "expert": patterns.expert_adjustment
            },
            "recommendations": [
                f"Best reading time: {_get_best_time_period(patterns)}",
                f"Optimal difficulty level: {_get_optimal_difficulty(patterns)}",
                f"Consistency level: {'High' if patterns.consistency_score > 0.7 else 'Medium' if patterns.consistency_score > 0.4 else 'Low'}"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user patterns: {str(e)}")


def _get_best_time_period(patterns) -> str:
    """Determine best time period for user"""
    factors = {
        "Morning (6-12)": patterns.morning_performance_factor,
        "Afternoon (12-18)": patterns.afternoon_performance_factor,
        "Evening (18-24)": patterns.evening_performance_factor,
        "Night (0-6)": patterns.night_performance_factor
    }
    return max(factors.items(), key=lambda x: x[1])[0]


def _get_optimal_difficulty(patterns) -> str:
    """Determine optimal difficulty for user"""
    if patterns.improvement_trend > 0.1:
        return "Advanced (you're improving!)"
    elif patterns.consistency_score > 0.7:
        return "Intermediate (consistent performance)"
    else:
        return "Beginner (focus on building consistency)"