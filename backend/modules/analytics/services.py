# backend/modules/analytics/services.py
"""
StudySprint 4.0 - Analytics Service
Business logic for advanced session analytics and performance tracking
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics

from shared.database import DatabaseService
from .models import SessionAnalytics, PageAnalytics, PerformanceMetrics, FocusLevel, ProductivityTrend
from core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AnalyticsService(DatabaseService):
    """Service for advanced session analytics"""
    
    def __init__(self):
        super().__init__(SessionAnalytics)
    
    def analyze_session(
        self,
        db: Session,
        session_id: int
    ) -> Dict[str, Any]:
        """Comprehensive session analysis"""
        try:
            from modules.sessions.models import Session as SessionModel
            
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                raise NotFoundException("Session", session_id)
            
            # Get existing analytics or create new
            analytics = db.query(SessionAnalytics).filter(
                SessionAnalytics.session_id == session_id
            ).first()
            
            if not analytics:
                analytics = SessionAnalytics(session_id=session_id)
                db.add(analytics)
            
            # Analyze focus patterns
            focus_analysis = self._analyze_focus_patterns(session)
            analytics.focus_periods = focus_analysis["periods"]
            analytics.distraction_events = focus_analysis["distractions"]
            analytics.focus_score = focus_analysis["score"]
            analytics.average_focus_duration = focus_analysis["average_duration"]
            
            # Analyze productivity
            productivity_analysis = self._analyze_productivity(session)
            analytics.productivity_score = productivity_analysis["score"]
            analytics.efficiency_rating = productivity_analysis["rating"]
            analytics.pages_per_minute_actual = productivity_analysis["actual_speed"]
            analytics.pages_per_minute_target = productivity_analysis["target_speed"]
            
            # Analyze break patterns
            break_analysis = self._analyze_break_patterns(session)
            analytics.break_frequency_score = break_analysis["frequency_score"]
            analytics.break_duration_average = break_analysis["average_duration"]
            analytics.break_timing_score = break_analysis["timing_score"]
            
            # Calculate consistency and improvement indicators
            analytics.consistency_score = self._calculate_session_consistency(session)
            analytics.improvement_indicators = self._analyze_improvement_indicators(db, session)
            analytics.fatigue_indicators = self._analyze_fatigue_indicators(session)
            
            # Generate optimization suggestions
            suggestions = self._generate_optimization_suggestions(session, analytics)
            analytics.optimization_suggestions = suggestions
            
            analytics.calculated_at = datetime.utcnow()
            db.commit()
            db.refresh(analytics)
            
            return {
                "session_id": session_id,
                "analytics": analytics,
                "focus_analysis": focus_analysis,
                "productivity_analysis": productivity_analysis,
                "break_analysis": break_analysis,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze session {session_id}: {e}")
            raise
    
    def analyze_focus_patterns(
        self,
        db: Session,
        session_id: int
    ) -> Dict[str, Any]:
        """Detailed focus pattern analysis"""
        try:
            analytics = self._get_session_analytics(db, session_id)
            
            focus_periods = analytics.focus_periods or []
            distraction_events = analytics.distraction_events or []
            
            if not focus_periods:
                return {"message": "No focus data available for this session"}
            
            # Calculate focus metrics
            total_focus_time = sum(period.get("duration", 0) for period in focus_periods)
            average_focus_duration = statistics.mean([p.get("duration", 0) for p in focus_periods])
            max_focus_duration = max([p.get("duration", 0) for p in focus_periods])
            
            # Focus consistency
            focus_durations = [p.get("duration", 0) for p in focus_periods]
            focus_consistency = 1.0 - (statistics.stdev(focus_durations) / average_focus_duration) if len(focus_durations) > 1 else 1.0
            
            # Distraction analysis
            distraction_frequency = len(distraction_events) / (total_focus_time / 60) if total_focus_time > 0 else 0
            
            return {
                "session_id": session_id,
                "focus_score": analytics.focus_score,
                "total_focus_time_minutes": total_focus_time,
                "average_focus_duration_minutes": average_focus_duration,
                "max_focus_duration_minutes": max_focus_duration,
                "focus_consistency_score": max(0.0, min(1.0, focus_consistency)),
                "distraction_count": len(distraction_events),
                "distraction_frequency_per_hour": distraction_frequency * 60,
                "focus_periods": focus_periods,
                "distraction_events": distraction_events,
                "recommendations": self._generate_focus_recommendations(analytics)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze focus patterns: {e}")
            raise
    
    def get_productivity_trends(
        self,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get productivity trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get performance metrics for the period
            metrics = db.query(PerformanceMetrics).filter(
                PerformanceMetrics.date >= start_date,
                PerformanceMetrics.date <= end_date
            ).order_by(PerformanceMetrics.date).all()
            
            if not metrics:
                return {"message": f"No productivity data available for the last {days} days"}
            
            # Calculate trends
            productivity_scores = [m.average_productivity_score for m in metrics]
            focus_scores = [m.average_focus_score for m in metrics]
            reading_speeds = [m.average_reading_speed for m in metrics]
            
            # Trend calculations
            productivity_trend = self._calculate_trend(productivity_scores)
            focus_trend = self._calculate_trend(focus_scores)
            speed_trend = self._calculate_trend(reading_speeds)
            
            # Peak performance analysis
            best_day = max(metrics, key=lambda m: m.average_productivity_score)
            worst_day = min(metrics, key=lambda m: m.average_productivity_score)
            
            return {
                "period_days": days,
                "data_points": len(metrics),
                "trends": {
                    "productivity": productivity_trend,
                    "focus": focus_trend,
                    "reading_speed": speed_trend
                },
                "averages": {
                    "productivity_score": statistics.mean(productivity_scores),
                    "focus_score": statistics.mean(focus_scores),
                    "reading_speed": statistics.mean(reading_speeds)
                },
                "best_performance": {
                    "date": best_day.date,
                    "productivity_score": best_day.average_productivity_score,
                    "study_time_minutes": best_day.total_study_time_minutes
                },
                "improvement_indicators": {
                    "consistency": self._calculate_consistency(productivity_scores),
                    "overall_trend": self._determine_overall_trend(productivity_trend, focus_trend, speed_trend)
                },
                "daily_data": [
                    {
                        "date": m.date,
                        "productivity_score": m.average_productivity_score,
                        "focus_score": m.average_focus_score,
                        "reading_speed": m.average_reading_speed,
                        "study_time_minutes": m.total_study_time_minutes
                    }
                    for m in metrics
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get productivity trends: {e}")
            raise
    
    def get_reading_speed_analytics(
        self,
        db: Session,
        content_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get reading speed analytics and trends"""
        try:
            from modules.sessions.models import Session as SessionModel
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get sessions within the date range
            query = db.query(SessionModel).filter(
                SessionModel.start_time >= start_date,
                SessionModel.start_time <= end_date,
                SessionModel.status == "completed",
                SessionModel.reading_speed > 0
            )
            
            if content_type:
                if content_type == "pdf":
                    query = query.filter(SessionModel.pdf_id.isnot(None))
            
            sessions = query.all()
            
            if not sessions:
                return {"message": f"No reading speed data available for the last {days} days"}
            
            # Extract reading speeds
            reading_speeds = [s.reading_speed for s in sessions]
            
            # Calculate statistics
            avg_speed = statistics.mean(reading_speeds)
            speed_std = statistics.stdev(reading_speeds) if len(reading_speeds) > 1 else 0
            min_speed = min(reading_speeds)
            max_speed = max(reading_speeds)
            
            # Speed trend analysis
            speed_trend = self._calculate_trend(reading_speeds)
            
            # Time of day analysis
            speed_by_hour = self._analyze_speed_by_time_of_day(sessions)
            
            # Content difficulty impact
            speed_variation = speed_std / avg_speed if avg_speed > 0 else 0
            
            return {
                "period_days": days,
               "session_count": len(sessions),
               "content_type": content_type or "all",
               "speed_statistics": {
                   "average_pages_per_minute": avg_speed,
                   "standard_deviation": speed_std,
                   "minimum_speed": min_speed,
                   "maximum_speed": max_speed,
                   "speed_consistency": max(0.0, 1.0 - speed_variation)
               },
               "trend_analysis": {
                   "trend": speed_trend,
                   "improvement_rate": self._calculate_improvement_rate(reading_speeds),
                   "consistency_trend": self._calculate_consistency_trend(reading_speeds)
               },
               "performance_patterns": {
                   "peak_performance_hour": max(speed_by_hour.items(), key=lambda x: x[1])[0] if speed_by_hour else None,
                   "speed_by_time_of_day": speed_by_hour,
                   "optimal_session_length": self._find_optimal_session_length(sessions)
               },
               "recommendations": self._generate_speed_recommendations(avg_speed, speed_trend, speed_by_hour)
           }
           
       except Exception as e:
           logger.error(f"❌ Failed to get reading speed analytics: {e}")
           raise
   
   def identify_learning_bottlenecks(
       self,
       db: Session,
       days: int = 30
   ) -> Dict[str, Any]:
       """Identify learning bottlenecks and inefficiencies"""
       try:
           from modules.sessions.models import Session as SessionModel
           from modules.pdfs.models import PDF
           
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           # Get recent sessions
           sessions = db.query(SessionModel).filter(
               SessionModel.start_time >= start_date,
               SessionModel.status == "completed"
           ).all()
           
           if not sessions:
               return {"message": f"No session data available for bottleneck analysis"}
           
           bottlenecks = []
           
           # 1. Low productivity sessions
           low_productivity_sessions = [s for s in sessions if s.productivity_score < 50]
           if len(low_productivity_sessions) > len(sessions) * 0.3:
               bottlenecks.append({
                   "type": "low_productivity",
                   "severity": "high",
                   "description": "High percentage of low-productivity sessions",
                   "affected_sessions": len(low_productivity_sessions),
                   "recommendations": [
                       "Take more frequent breaks",
                       "Study during peak energy hours",
                       "Eliminate distractions in study environment"
                   ]
               })
           
           # 2. Slow reading speed trend
           reading_speeds = [s.reading_speed for s in sessions if s.reading_speed > 0]
           if reading_speeds:
               speed_trend = self._calculate_trend(reading_speeds)
               if speed_trend < -0.1:
                   bottlenecks.append({
                       "type": "declining_speed",
                       "severity": "medium",
                       "description": "Reading speed is declining over time",
                       "trend_value": speed_trend,
                       "recommendations": [
                           "Practice speed reading techniques",
                           "Ensure adequate rest between sessions",
                           "Check if content difficulty has increased"
                       ]
                   })
           
           # 3. Inconsistent focus patterns
           focus_scores = [s.focus_score for s in sessions if s.focus_score > 0]
           if focus_scores:
               focus_consistency = 1.0 - (statistics.stdev(focus_scores) / statistics.mean(focus_scores))
               if focus_consistency < 0.6:
                   bottlenecks.append({
                       "type": "inconsistent_focus",
                       "severity": "medium",
                       "description": "Focus levels are inconsistent across sessions",
                       "consistency_score": focus_consistency,
                       "recommendations": [
                           "Establish a consistent study routine",
                           "Practice mindfulness or meditation",
                           "Optimize study environment for focus"
                       ]
                   })
           
           # 4. Session length issues
           session_lengths = [s.total_duration_seconds / 60 for s in sessions]
           avg_length = statistics.mean(session_lengths)
           
           if avg_length > 120:
               bottlenecks.append({
                   "type": "excessive_session_length",
                   "severity": "medium",
                   "description": "Study sessions are consistently too long",
                   "average_length_minutes": avg_length,
                   "recommendations": [
                       "Break long sessions into 60-90 minute chunks",
                       "Take 15-minute breaks between sessions",
                       "Use Pomodoro technique for better focus"
                   ]
               })
           elif avg_length < 30:
               bottlenecks.append({
                   "type": "insufficient_session_length",
                   "severity": "low",
                   "description": "Study sessions may be too short for deep learning",
                   "average_length_minutes": avg_length,
                   "recommendations": [
                       "Aim for 45-60 minute focused sessions",
                       "Allow warm-up time to get into flow state",
                       "Plan session content in advance"
                   ]
               })
           
           # Overall assessment
           severity_counts = {"high": 0, "medium": 0, "low": 0}
           for bottleneck in bottlenecks:
               severity_counts[bottleneck["severity"]] += 1
           
           overall_health = "excellent"
           if severity_counts["high"] > 0:
               overall_health = "needs_attention"
           elif severity_counts["medium"] > 1:
               overall_health = "room_for_improvement"
           elif severity_counts["medium"] > 0 or severity_counts["low"] > 0:
               overall_health = "good"
           
           return {
               "analysis_period_days": days,
               "sessions_analyzed": len(sessions),
               "overall_health": overall_health,
               "bottlenecks_found": len(bottlenecks),
               "severity_breakdown": severity_counts,
               "bottlenecks": bottlenecks,
               "summary": {
                   "primary_issues": [b["type"] for b in bottlenecks if b["severity"] == "high"],
                   "improvement_areas": [b["type"] for b in bottlenecks if b["severity"] == "medium"],
                   "optimization_opportunities": [b["type"] for b in bottlenecks if b["severity"] == "low"]
               },
               "action_plan": self._generate_action_plan(bottlenecks)
           }
           
       except Exception as e:
           logger.error(f"❌ Failed to identify learning bottlenecks: {e}")
           raise
   
   def calculate_daily_performance_metrics(
       self,
       db: Session,
       date: datetime = None
   ) -> PerformanceMetrics:
       """Calculate and store daily performance metrics"""
       try:
           if date is None:
               date = datetime.utcnow().date()
           
           from modules.sessions.models import Session as SessionModel
           
           # Get sessions for the day
           start_of_day = datetime.combine(date, datetime.min.time())
           end_of_day = datetime.combine(date, datetime.max.time())
           
           sessions = db.query(SessionModel).filter(
               SessionModel.start_time >= start_of_day,
               SessionModel.start_time <= end_of_day,
               SessionModel.status == "completed"
           ).all()
           
           # Calculate metrics
           total_study_time = sum(s.active_duration_seconds for s in sessions) // 60
           total_active_time = sum(s.active_duration_seconds for s in sessions) // 60
           total_pages = sum(s.pages_covered for s in sessions)
           session_count = len(sessions)
           
           # Average scores
           focus_scores = [s.focus_score for s in sessions if s.focus_score > 0]
           productivity_scores = [s.productivity_score for s in sessions if s.productivity_score > 0]
           reading_speeds = [s.reading_speed for s in sessions if s.reading_speed > 0]
           
           avg_focus = statistics.mean(focus_scores) if focus_scores else 0
           avg_productivity = statistics.mean(productivity_scores) if productivity_scores else 0
           avg_reading_speed = statistics.mean(reading_speeds) if reading_speeds else 0
           
           # Consistency score
           consistency = self._calculate_consistency(productivity_scores) if len(productivity_scores) > 1 else 1.0
           
           # Get or create performance metrics record
           metrics = db.query(PerformanceMetrics).filter(
               PerformanceMetrics.date == start_of_day
           ).first()
           
           if not metrics:
               metrics = PerformanceMetrics(date=start_of_day)
               db.add(metrics)
           
           # Update metrics
           metrics.total_study_time_minutes = total_study_time
           metrics.total_active_time_minutes = total_active_time
           metrics.total_pages_covered = total_pages
           metrics.session_count = session_count
           metrics.average_focus_score = avg_focus
           metrics.average_productivity_score = avg_productivity
           metrics.average_reading_speed = avg_reading_speed
           metrics.consistency_score = consistency
           metrics.calculated_at = datetime.utcnow()
           
           # Calculate trends
           yesterday = date - timedelta(days=1)
           yesterday_metrics = db.query(PerformanceMetrics).filter(
               PerformanceMetrics.date == datetime.combine(yesterday, datetime.min.time())
           ).first()
           
           if yesterday_metrics:
               productivity_change = avg_productivity - yesterday_metrics.average_productivity_score
               focus_change = avg_focus - yesterday_metrics.average_focus_score
               speed_change = avg_reading_speed - yesterday_metrics.average_reading_speed
               
               metrics.productivity_trend = self._determine_trend_from_change(productivity_change)
               metrics.focus_trend = self._determine_trend_from_change(focus_change)
               metrics.speed_trend = self._determine_trend_from_change(speed_change)
               metrics.efficiency_vs_previous_day = productivity_change / 100
           
           db.commit()
           db.refresh(metrics)
           
           logger.info(f"✅ Calculated daily metrics for {date}: {session_count} sessions, {total_study_time}min study time")
           return metrics
           
       except Exception as e:
           db.rollback()
           logger.error(f"❌ Failed to calculate daily performance metrics: {e}")
           raise
   
   # Helper methods
   
   def _get_session_analytics(self, db: Session, session_id: int) -> SessionAnalytics:
       """Get session analytics, creating if not exists"""
       analytics = db.query(SessionAnalytics).filter(
           SessionAnalytics.session_id == session_id
       ).first()
       
       if not analytics:
           self.analyze_session(db, session_id)
           analytics = db.query(SessionAnalytics).filter(
               SessionAnalytics.session_id == session_id
           ).first()
       
       return analytics
   
   def _analyze_focus_patterns(self, session) -> Dict[str, Any]:
       """Analyze focus patterns from session data"""
       total_duration = session.active_duration_seconds / 60
       
       if total_duration > 0:
           avg_focus_period = min(25, total_duration / 3)
           num_periods = max(1, int(total_duration / avg_focus_period))
           
           periods = []
           for i in range(num_periods):
               period_duration = avg_focus_period * (0.8 + 0.4 * (session.focus_score / 100))
               periods.append({
                   "start_minute": i * avg_focus_period,
                   "duration": period_duration,
                   "intensity": 0.6 + 0.4 * (session.focus_score / 100)
               })
           
           distraction_count = max(0, int((1 - session.focus_score / 100) * total_duration / 10))
           distractions = [
               {
                   "minute": i * (total_duration / max(1, distraction_count)),
                   "duration": 1.5,
                   "type": "unknown"
               }
               for i in range(distraction_count)
           ]
           
           focus_score = session.focus_score / 100
           avg_duration = statistics.mean([p["duration"] for p in periods]) if periods else 0
           
       else:
           periods = []
           distractions = []
           focus_score = 0.0
           avg_duration = 0.0
       
       return {
           "periods": periods,
           "distractions": distractions,
           "score": focus_score,
           "average_duration": avg_duration
       }
   
   def _analyze_productivity(self, session) -> Dict[str, Any]:
       """Analyze productivity metrics"""
       actual_speed = session.reading_speed
       target_speed = 1.0
       
       productivity_score = session.productivity_score / 100
       
       if productivity_score >= 0.8:
           rating = "excellent"
       elif productivity_score >= 0.6:
           rating = "good"
       elif productivity_score >= 0.4:
           rating = "fair"
       else:
           rating = "poor"
       
       return {
           "score": productivity_score,
           "rating": rating,
           "actual_speed": actual_speed,
           "target_speed": target_speed,
           "efficiency_ratio": actual_speed / target_speed if target_speed > 0 else 0
       }
   
   def _analyze_break_patterns(self, session) -> Dict[str, Any]:
       """Analyze break patterns"""
       total_time = session.total_duration_seconds / 60
       active_time = session.active_duration_seconds / 60
       break_time = session.break_duration_seconds / 60
       
       if total_time > 0:
           break_ratio = break_time / total_time
           optimal_ratio = 0.2
           frequency_score = 1.0 - abs(break_ratio - optimal_ratio) / optimal_ratio
           frequency_score = max(0.0, min(1.0, frequency_score))
           
           estimated_breaks = max(1, int(break_time / 5))
           avg_duration = break_time / estimated_breaks if estimated_breaks > 0 else 0
           timing_score = 0.8 if total_time > 60 else 0.6
       else:
           frequency_score = 0.5
           avg_duration = 0.0
           timing_score = 0.5
       
       return {
           "frequency_score": frequency_score,
           "average_duration": avg_duration,
           "timing_score": timing_score
       }
   
   def _calculate_session_consistency(self, session) -> float:
       """Calculate consistency score for a session"""
       base_consistency = 0.7
       productivity_factor = session.productivity_score / 100 * 0.3
       return min(1.0, base_consistency + productivity_factor)
   
   def _analyze_improvement_indicators(self, db: Session, session) -> Dict[str, Any]:
       """Analyze improvement indicators"""
       from modules.sessions.models import Session as SessionModel
       
       recent_sessions = db.query(SessionModel).filter(
           SessionModel.start_time >= datetime.utcnow() - timedelta(days=7),
           SessionModel.status == "completed",
           SessionModel.id != session.id
       ).order_by(SessionModel.start_time.desc()).limit(10).all()
       
       if not recent_sessions:
           return {"trend": "insufficient_data"}
       
       recent_productivity = statistics.mean([s.productivity_score for s in recent_sessions])
       recent_focus = statistics.mean([s.focus_score for s in recent_sessions])
       recent_speed = statistics.mean([s.reading_speed for s in recent_sessions if s.reading_speed > 0])
       
       indicators = {
           "productivity_improvement": session.productivity_score - recent_productivity,
           "focus_improvement": session.focus_score - recent_focus,
           "speed_improvement": session.reading_speed - recent_speed if recent_speed > 0 else 0,
           "trend": "improving" if session.productivity_score > recent_productivity else "stable"
       }
       
       return indicators
   
   def _analyze_fatigue_indicators(self, session) -> Dict[str, Any]:
       """Analyze fatigue indicators"""
       indicators = {}
       
       session_length_minutes = session.total_duration_seconds / 60
       if session_length_minutes > 120:
           indicators["excessive_length"] = True
           indicators["fatigue_risk"] = "high"
       elif session_length_minutes > 90:
           indicators["fatigue_risk"] = "medium"
       else:
           indicators["fatigue_risk"] = "low"
       
       if session.productivity_score < 50:
           indicators["low_productivity"] = True
       
       if session.focus_score < 50:
           indicators["focus_issues"] = True
       
       return indicators
   
   def _generate_optimization_suggestions(self, session, analytics) -> List[str]:
       """Generate optimization suggestions"""
       suggestions = []
       
       if analytics.focus_score < 0.6:
           suggestions.append("Try the Pomodoro technique: 25 minutes of focused study followed by 5-minute breaks")
           suggestions.append("Eliminate distractions in your study environment")
       
       if analytics.productivity_score < 0.5:
           suggestions.append("Consider studying during your peak energy hours")
           suggestions.append("Break large tasks into smaller, manageable chunks")
       
       if analytics.pages_per_minute_actual < analytics.pages_per_minute_target * 0.8:
           suggestions.append("Practice active reading techniques to improve comprehension and speed")
           suggestions.append("Preview material before detailed reading")
       
       if analytics.break_frequency_score < 0.6:
           suggestions.append("Take regular breaks to maintain focus and prevent fatigue")
       
       if analytics.break_duration_average > 10:
           suggestions.append("Keep breaks shorter (5-10 minutes) to maintain momentum")
       
       session_length = session.total_duration_seconds / 60
       if session_length > 120:
           suggestions.append("Consider shorter study sessions (60-90 minutes) for better retention")
       elif session_length < 30:
           suggestions.append("Try longer study sessions (45-60 minutes) for deeper focus")
       
       return suggestions[:5]
   
   def _calculate_trend(self, values: List[float]) -> float:
       """Calculate trend (-1 to 1)"""
       if len(values) < 2:
           return 0.0
       
       n = len(values)
       x_values = list(range(n))
       
       sum_x = sum(x_values)
       sum_y = sum(values)
       sum_xy = sum(x * y for x, y in zip(x_values, values))
       sum_x2 = sum(x * x for x in x_values)
       
       if n * sum_x2 - sum_x * sum_x == 0:
           return 0.0
       
       slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
       
       max_change = max(values) - min(values)
       if max_change == 0:
           return 0.0
       
       normalized_slope = slope / (max_change / n)
       return max(-1.0, min(1.0, normalized_slope))
   
   def _calculate_consistency(self, values: List[float]) -> float:
       """Calculate consistency score"""
       if len(values) < 2:
           return 1.0
       
       mean_val = statistics.mean(values)
       if mean_val == 0:
           return 1.0
       
       coefficient_of_variation = statistics.stdev(values) / mean_val
       consistency = max(0.0, 1.0 - coefficient_of_variation)
       return min(1.0, consistency)
   
   def _determine_overall_trend(self, productivity_trend: float, focus_trend: float, speed_trend: float) -> str:
       """Determine overall trend"""
       avg_trend = (productivity_trend + focus_trend + speed_trend) / 3
       
       if avg_trend > 0.1:
           return "improving"
       elif avg_trend < -0.1:
           return "declining"
       else:
           return "stable"
   
   def _analyze_speed_by_time_of_day(self, sessions) -> Dict[int, float]:
       """Analyze speed by hour"""
       speed_by_hour = {}
       
       for session in sessions:
           hour = session.start_time.hour
           if hour not in speed_by_hour:
               speed_by_hour[hour] = []
           speed_by_hour[hour].append(session.reading_speed)
       
       return {
           hour: statistics.mean(speeds)
           for hour, speeds in speed_by_hour.items()
       }
   
   def _find_optimal_session_length(self, sessions) -> int:
       """Find optimal session length"""
       if not sessions:
           return 60
       
       length_groups = {30: [], 60: [], 90: [], 120: []}
       
       for session in sessions:
           length = session.total_duration_seconds / 60
           if length <= 30:
               length_groups[30].append(session.productivity_score)
           elif length <= 60:
               length_groups[60].append(session.productivity_score)
           elif length <= 90:
               length_groups[90].append(session.productivity_score)
           else:
               length_groups[120].append(session.productivity_score)
       
       best_length = 60
       best_productivity = 0
       
       for length, productivities in length_groups.items():
           if productivities:
               avg_productivity = statistics.mean(productivities)
               if avg_productivity > best_productivity:
                   best_productivity = avg_productivity
                   best_length = length
       
       return best_length
   
   def _calculate_improvement_rate(self, values: List[float]) -> float:
       """Calculate improvement rate"""
       if len(values) < 2:
           return 0.0
       
       n = len(values)
       first_quarter = values[:n//4] if n >= 4 else values[:1]
       last_quarter = values[-n//4:] if n >= 4 else values[-1:]
       
       if not first_quarter or not last_quarter:
           return 0.0
       
       first_avg = statistics.mean(first_quarter)
       last_avg = statistics.mean(last_quarter)
       
       if first_avg == 0:
           return 0.0
       
       return (last_avg - first_avg) / first_avg
   
   def _calculate_consistency_trend(self, values: List[float]) -> str:
       """Calculate consistency trend"""
       if len(values) < 6:
           return "insufficient_data"
       
       mid = len(values) // 2
       first_half = values[:mid]
       second_half = values[mid:]
       
       first_consistency = self._calculate_consistency(first_half)
       second_consistency = self._calculate_consistency(second_half)
       
       diff = second_consistency - first_consistency
       
       if diff > 0.1:
           return "improving"
       elif diff < -0.1:
           return "declining"
       else:
           return "stable"
   
   def _generate_focus_recommendations(self, analytics: SessionAnalytics) -> List[str]:
       """Generate focus recommendations"""
       recommendations = []
       
       if analytics.focus_score < 0.5:
           recommendations.extend([
               "Try meditation or mindfulness exercises before studying",
               "Remove digital distractions from study area",
               "Use background music or white noise if it helps concentration"
           ])
       
       if analytics.average_focus_duration < 15:
           recommendations.append("Gradually increase focus periods - start with 15-20 minutes")
       
       if len(analytics.distraction_events or []) > 5:
           recommendations.append("Identify and eliminate common distraction sources")
       
       return recommendations
   
   def _generate_speed_recommendations(
       self,
       avg_speed: float,
       speed_trend: float,
       speed_by_hour: Dict[int, float]
   ) -> List[str]:
       """Generate speed recommendations"""
       recommendations = []
       
       if avg_speed < 0.8:
           recommendations.extend([
               "Practice skimming techniques for initial content overview",
               "Focus on key concepts rather than reading every word",
               "Use a pointer (finger/pen) to guide your reading pace"
           ])
       
       if speed_trend < -0.1:
           recommendations.extend([
               "Ensure adequate rest - fatigue significantly impacts reading speed",
               "Check if content difficulty has increased recently",
               "Consider speed reading exercises and techniques"
           ])
       
       if speed_by_hour:
           peak_hour = max(speed_by_hour.items(), key=lambda x: x[1])[0]
           recommendations.append(f"Schedule intensive reading during your peak hour: {peak_hour}:00")
       
       return recommendations
   
   def _generate_action_plan(self, bottlenecks: List[Dict]) -> List[Dict[str, Any]]:
       """Generate action plan"""
       action_plan = []
       
       high_priority = [b for b in bottlenecks if b["severity"] == "high"]
       medium_priority = [b for b in bottlenecks if b["severity"] == "medium"]
       
       for bottleneck in high_priority:
           action_plan.append({
               "priority": "immediate",
               "issue": bottleneck["type"],
               "actions": bottleneck["recommendations"][:2],
               "timeframe": "1-3 days"
           })
       
       for bottleneck in medium_priority:
           action_plan.append({
               "priority": "short_term",
               "issue": bottleneck["type"],
               "actions": bottleneck["recommendations"][:1],
               "timeframe": "1-2 weeks"
           })
       
       return action_plan
   
   def _determine_trend_from_change(self, change: float) -> str:
       """Determine trend from change"""
       if change > 5:
           return ProductivityTrend.IMPROVING.value
       elif change < -5:
           return ProductivityTrend.DECLINING.value
       else:
           return ProductivityTrend.STABLE.value


# Global service instance
analytics_service = AnalyticsService()