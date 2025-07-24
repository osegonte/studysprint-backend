# backend/modules/estimation/services.py
"""
StudySprint 4.0 - Estimation Service
Business logic for multi-level time estimation system
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import statistics

from shared.database import DatabaseService
from .models import EstimationData, EstimationHistory, UserReadingPatterns, ContentType, EstimationConfidence
from .schemas import EstimationCreate, EstimationUpdate, EstimationResponse
from core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class EstimationService(DatabaseService):
    """Service for multi-level time estimation"""
    
    def __init__(self):
        super().__init__(EstimationData)
        self.algorithm_version = "1.0"
    
    def estimate_pdf_completion_time(
        self,
        db: Session,
        pdf_id: int,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Estimate PDF completion time with confidence scoring"""
        try:
            # Get PDF information
            from modules.pdfs.models import PDF
            pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
            if not pdf:
                raise NotFoundException("PDF", pdf_id)
            
            # Get or create user reading patterns
            patterns = self._get_user_reading_patterns(db, ContentType.PDF)
            
            # Calculate base estimation
            base_time = self._calculate_base_estimation(
                content_type=ContentType.PDF,
                content_size=pdf.page_count,
                patterns=patterns
            )
            
            # Apply context factors
            context_factors = self._calculate_context_factors(
                user_context or {},
                patterns
            )
            
            adjusted_time = base_time * context_factors['total_factor']
            
            # Calculate confidence
            confidence_score, confidence_level = self._calculate_confidence(
                content_type=ContentType.PDF,
                patterns=patterns,
                context_factors=context_factors
            )
            
            # Store estimation
            estimation = self._store_estimation(
                db=db,
                content_type=ContentType.PDF,
                content_id=pdf_id,
                estimated_time=adjusted_time,
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                factors=context_factors
            )
            
            return {
                "pdf_id": pdf_id,
                "estimated_time_minutes": adjusted_time,
                "estimated_time_formatted": self._format_time(adjusted_time),
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
                "factors": context_factors,
                "estimation_id": estimation.id,
                "page_count": pdf.page_count,
                "estimated_pages_per_minute": patterns.average_speed_pages_per_minute,
                "completion_date_estimate": datetime.utcnow() + timedelta(minutes=adjusted_time)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to estimate PDF completion time: {e}")
            raise
    
    def estimate_topic_completion_time(
        self,
        db: Session,
        topic_id: int,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Estimate topic completion time based on associated PDFs"""
        try:
            # Get topic and associated PDFs
            from modules.topics.models import Topic
            from modules.pdfs.models import PDF
            
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            if not topic:
                raise NotFoundException("Topic", topic_id)
            
            pdfs = db.query(PDF).filter(PDF.topic_id == topic_id).all()
            
            if not pdfs:
                return {
                    "topic_id": topic_id,
                    "estimated_time_minutes": 0.0,
                    "confidence_level": "low",
                    "message": "No PDFs associated with this topic"
                }
            
            # Calculate individual PDF estimates
            total_time = 0.0
            pdf_estimates = []
            confidence_scores = []
            
            for pdf in pdfs:
                pdf_estimate = self.estimate_pdf_completion_time(db, pdf.id, user_context)
                total_time += pdf_estimate["estimated_time_minutes"]
                pdf_estimates.append(pdf_estimate)
                confidence_scores.append(pdf_estimate["confidence_score"])
            
            # Calculate overall confidence
            overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
            confidence_level = self._score_to_confidence_level(overall_confidence)
            
            return {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "estimated_time_minutes": total_time,
                "estimated_time_formatted": self._format_time(total_time),
                "confidence_score": overall_confidence,
                "confidence_level": confidence_level,
                "pdf_count": len(pdfs),
                "pdf_estimates": pdf_estimates,
                "completion_date_estimate": datetime.utcnow() + timedelta(minutes=total_time),
                "remaining_pages": sum(pdf.page_count - pdf.completion_percentage/100 * pdf.page_count for pdf in pdfs)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to estimate topic completion time: {e}")
            raise
    
    def estimate_app_total_time(
        self,
        db: Session,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Estimate total remaining work across all content"""
        try:
            from modules.topics.models import Topic
            
            # Get all active topics
            topics = db.query(Topic).filter(
                Topic.is_active == True,
                Topic.is_archived == False
            ).all()
            
            total_time = 0.0
            topic_estimates = []
            confidence_scores = []
            
            for topic in topics:
                topic_estimate = self.estimate_topic_completion_time(db, topic.id, user_context)
                total_time += topic_estimate["estimated_time_minutes"]
                topic_estimates.append(topic_estimate)
                confidence_scores.append(topic_estimate["confidence_score"])
            
            # Calculate statistics
            overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
            
            # Get total pages and completion
            total_pages = sum(topic.total_pages for topic in topics)
            completed_pages = sum(topic.completed_pages for topic in topics)
            completion_percentage = (completed_pages / total_pages * 100) if total_pages > 0 else 0
            
            return {
                "total_estimated_time_minutes": total_time,
                "total_estimated_time_formatted": self._format_time(total_time),
                "confidence_score": overall_confidence,
                "confidence_level": self._score_to_confidence_level(overall_confidence),
                "topic_count": len(topics),
                "total_pages": total_pages,
                "completed_pages": completed_pages,
                "completion_percentage": completion_percentage,
                "estimated_completion_date": datetime.utcnow() + timedelta(minutes=total_time),
                "topic_estimates": topic_estimates,
                "daily_study_recommendation": self._calculate_daily_recommendation(total_time)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to estimate app total time: {e}")
            raise
    
    def update_estimation_from_session(
        self,
        db: Session,
        session_id: int
    ) -> Dict[str, Any]:
        """Update estimations based on actual session performance"""
        try:
            from modules.sessions.models import Session as SessionModel
            
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                raise NotFoundException("Session", session_id)
            
            # Only process completed sessions
            if session.status != "completed":
                return {"message": "Session must be completed to update estimations"}
            
            # Calculate actual performance metrics
            actual_time_minutes = session.active_duration_seconds / 60
            pages_covered = session.pages_covered
            reading_speed = pages_covered / actual_time_minutes if actual_time_minutes > 0 else 0
            
            # Update user reading patterns
            patterns = self._get_user_reading_patterns(db, ContentType.PDF)
            self._update_reading_patterns(db, patterns, session, reading_speed)
            
            # Record estimation history if there was an estimation
            content_id = session.pdf_id or session.topic_id
            content_type = ContentType.PDF if session.pdf_id else ContentType.TOPIC
            
            if content_id:
                self._record_estimation_accuracy(
                    db=db,
                    content_type=content_type,
                    content_id=content_id,
                    session_id=session_id,
                    actual_time_minutes=actual_time_minutes
                )
            
            # Recalculate related estimations
            updated_estimations = self._recalculate_affected_estimations(db, session)
            
            return {
                "session_id": session_id,
                "actual_time_minutes": actual_time_minutes,
                "reading_speed": reading_speed,
                "patterns_updated": True,
                "estimations_recalculated": len(updated_estimations),
                "updated_estimations": updated_estimations
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update estimation from session: {e}")
            raise
    
    def get_estimation_accuracy(self, db: Session) -> Dict[str, Any]:
        """Get estimation accuracy analytics"""
        try:
            # Get recent estimation history
            recent_history = db.query(EstimationHistory).filter(
                EstimationHistory.recorded_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if not recent_history:
                return {
                    "message": "No recent estimation data available",
                    "accuracy_score": 0.0,
                    "sample_size": 0
                }
            
            # Calculate accuracy metrics
            accuracy_scores = [h.accuracy_score for h in recent_history]
            
            overall_accuracy = statistics.mean(accuracy_scores)
            accuracy_std = statistics.stdev(accuracy_scores) if len(accuracy_scores) > 1 else 0
            
            # Accuracy by content type
            by_content_type = {}
            for history in recent_history:
                content_type = history.estimation.content_type
                if content_type not in by_content_type:
                    by_content_type[content_type] = []
                by_content_type[content_type].append(history.accuracy_score)
            
            content_type_accuracy = {
                ct: statistics.mean(scores) 
                for ct, scores in by_content_type.items()
            }
            
            # Trending analysis
            recent_scores = sorted(accuracy_scores)[-10:]  # Last 10 estimates
            trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
            
            return {
                "overall_accuracy": overall_accuracy,
                "accuracy_standard_deviation": accuracy_std,
                "sample_size": len(recent_history),
                "accuracy_by_content_type": content_type_accuracy,
                "trend": trend,
                "confidence_level": "high" if overall_accuracy > 0.8 else "medium" if overall_accuracy > 0.6 else "low"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get estimation accuracy: {e}")
            raise
    
    # Helper methods
    
    def _get_user_reading_patterns(
        self,
        db: Session,
        content_type: ContentType
    ) -> UserReadingPatterns:
        """Get or create user reading patterns"""
        patterns = db.query(UserReadingPatterns).filter(
            UserReadingPatterns.content_type == content_type.value
        ).first()
        
        if not patterns:
            patterns = UserReadingPatterns(
                content_type=content_type.value,
                average_speed_pages_per_minute=1.0,
                total_study_sessions=0
            )
            db.add(patterns)
            db.commit()
            db.refresh(patterns)
        
        return patterns
    
    def _calculate_base_estimation(
        self,
        content_type: ContentType,
        content_size: int,
        patterns: UserReadingPatterns
    ) -> float:
        """Calculate base time estimation"""
        if content_type == ContentType.PDF:
            return content_size / patterns.average_speed_pages_per_minute
        return content_size * 2.0  # Default fallback
    
    def _calculate_context_factors(
        self,
        user_context: Dict[str, Any],
        patterns: UserReadingPatterns
    ) -> Dict[str, Any]:
        """Calculate context-based adjustment factors"""
        factors = {
            "time_of_day_factor": 1.0,
            "difficulty_factor": 1.0,
            "energy_factor": 1.0,
            "consistency_factor": 1.0
        }
        
        # Time of day factor
        current_hour = datetime.now().hour
        factors["time_of_day_factor"] = patterns.get_time_factor(current_hour)
        
        # Difficulty factor
        difficulty = user_context.get("difficulty", "intermediate")
        difficulty_map = {
            "beginner": patterns.beginner_adjustment,
            "intermediate": patterns.intermediate_adjustment,
            "advanced": patterns.advanced_adjustment,
            "expert": patterns.expert_adjustment
        }
        factors["difficulty_factor"] = difficulty_map.get(difficulty, 1.0)
        
        # User energy factor
        energy_level = user_context.get("energy_level", 0.8)
        factors["energy_factor"] = 0.5 + (energy_level * 0.5)
        
        # Consistency factor
        factors["consistency_factor"] = max(0.7, patterns.consistency_score)
        
        # Calculate total factor
        factors["total_factor"] = (
            factors["time_of_day_factor"] *
            factors["difficulty_factor"] *
            factors["energy_factor"] *
            factors["consistency_factor"]
        )
        
        return factors
    
    def _calculate_confidence(
        self,
        content_type: ContentType,
        patterns: UserReadingPatterns,
        context_factors: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Calculate estimation confidence"""
        base_confidence = 0.5
        
        # More sessions = higher confidence
        session_confidence = min(0.3, patterns.total_study_sessions * 0.01)
        
        # Consistency boosts confidence
        consistency_confidence = patterns.consistency_score * 0.2
        
        # Stable factors boost confidence
        factor_stability = 1.0 - abs(context_factors["total_factor"] - 1.0)
        stability_confidence = factor_stability * 0.2
        
        total_confidence = base_confidence + session_confidence + consistency_confidence + stability_confidence
        total_confidence = max(0.0, min(1.0, total_confidence))
        
        return total_confidence, self._score_to_confidence_level(total_confidence)
    
    def _score_to_confidence_level(self, score: float) -> str:
        """Convert confidence score to level"""
        if score >= 0.8:
            return EstimationConfidence.VERY_HIGH.value
        elif score >= 0.6:
            return EstimationConfidence.HIGH.value
        elif score >= 0.4:
            return EstimationConfidence.MEDIUM.value
        else:
            return EstimationConfidence.LOW.value
    
    def _store_estimation(
        self,
        db: Session,
        content_type: ContentType,
        content_id: int,
        estimated_time: float,
        confidence_score: float,
        confidence_level: str,
        factors: Dict[str, Any]
    ) -> EstimationData:
        """Store estimation data"""
        # Check for existing estimation
        existing = db.query(EstimationData).filter(
            EstimationData.content_type == content_type.value,
            EstimationData.content_id == content_id
        ).first()
        
        if existing:
            # Update existing
            existing.estimated_time_minutes = estimated_time
            existing.confidence_score = confidence_score
            existing.confidence_level = confidence_level
            existing.estimation_factors = factors
            existing.updated_at = datetime.utcnow()
            estimation = existing
        else:
            # Create new
            estimation = EstimationData(
                content_type=content_type.value,
                content_id=content_id,
                estimated_time_minutes=estimated_time,
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                estimation_factors=factors,
                algorithm_version=self.algorithm_version
            )
            db.add(estimation)
        
        db.commit()
        db.refresh(estimation)
        return estimation
    
    def _format_time(self, minutes: float) -> str:
        """Format time in human-readable format"""
        if minutes < 60:
            return f"{int(minutes)}m"
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"
    
    def _update_reading_patterns(
        self,
        db: Session,
        patterns: UserReadingPatterns,
        session,
        reading_speed: float
    ):
        """Update user reading patterns based on session"""
        if reading_speed > 0:
            # Update running average
            total_sessions = patterns.total_study_sessions
            current_avg = patterns.average_speed_pages_per_minute
            
            # Weighted average (recent sessions have more influence)
            weight = min(0.1, 1.0 / max(1, total_sessions))
            new_avg = current_avg * (1 - weight) + reading_speed * weight
            
            patterns.average_speed_pages_per_minute = new_avg
            patterns.total_study_sessions += 1
            patterns.last_updated = datetime.utcnow()
            
            # Update min/max speeds
            if reading_speed > patterns.peak_speed_pages_per_minute:
                patterns.peak_speed_pages_per_minute = reading_speed
            if reading_speed < patterns.minimum_speed_pages_per_minute:
                patterns.minimum_speed_pages_per_minute = reading_speed
            
            db.commit()
    
    def _record_estimation_accuracy(
        self,
        db: Session,
        content_type: ContentType,
        content_id: int,
        session_id: int,
        actual_time_minutes: float
    ):
        """Record estimation accuracy for learning"""
        # Find the estimation
        estimation = db.query(EstimationData).filter(
            EstimationData.content_type == content_type.value,
            EstimationData.content_id == content_id
        ).first()
        
        if estimation:
            # Create history record
            history = EstimationHistory(
                estimation_id=estimation.id,
                session_id=session_id,
                estimated_time_minutes=estimation.estimated_time_minutes,
                actual_time_minutes=actual_time_minutes,
                time_of_day=datetime.now().hour,
                user_energy_level=0.8  # Default, could be enhanced
            )
            
            history.calculate_accuracy()
            db.add(history)
            db.commit()
    
    def _recalculate_affected_estimations(self, db: Session, session) -> List[Dict]:
        """Recalculate estimations affected by the session"""
        updated = []
        
        # If PDF session, recalculate PDF and its topic
        if session.pdf_id:
            pdf_estimate = self.estimate_pdf_completion_time(db, session.pdf_id)
            updated.append({"type": "pdf", "id": session.pdf_id, "estimate": pdf_estimate})
            
            # Also recalculate topic if PDF belongs to one
            from modules.pdfs.models import PDF
            pdf = db.query(PDF).filter(PDF.id == session.pdf_id).first()
            if pdf and pdf.topic_id:
                topic_estimate = self.estimate_topic_completion_time(db, pdf.topic_id)
                updated.append({"type": "topic", "id": pdf.topic_id, "estimate": topic_estimate})
        
        return updated
    
    def _calculate_daily_recommendation(self, total_minutes: float) -> Dict[str, Any]:
        """Calculate daily study time recommendation"""
        # Assume user wants to complete in 30 days by default
        target_days = 30
        daily_minutes = total_minutes / target_days
        
        return {
            "daily_minutes_recommended": int(daily_minutes),
            "daily_time_formatted": self._format_time(daily_minutes),
            "completion_in_days": target_days,
            "sessions_per_day": max(1, int(daily_minutes // 60)),
            "feasibility": "high" if daily_minutes <= 120 else "medium" if daily_minutes <= 240 else "low"
        }


# Global service instance
estimation_service = EstimationService()