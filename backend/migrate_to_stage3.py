# backend/migrate_to_stage3.py
"""
StudySprint 4.0 - Stage 2 to Stage 3 Migration
Database migration script for new Stage 3 models
"""
import asyncio
from database import SessionLocal, Base, engine
from modules.estimation.models import EstimationData, EstimationHistory, UserReadingPatterns
from modules.analytics.models import SessionAnalytics, PageAnalytics, PerformanceMetrics
import logging

logger = logging.getLogger(__name__)


async def migrate_to_stage3():
    """Migrate database from Stage 2 to Stage 3"""
    print("🔄 Migrating StudySprint 4.0 from Stage 2 to Stage 3...")
    
    try:
        # Create new tables for Stage 3
        print("📊 Creating Stage 3 database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Stage 3 tables created successfully")
        
        db = SessionLocal()
        
        # Initialize user reading patterns for existing users
        print("👤 Initializing user reading patterns...")
        from modules.estimation.models import ContentType
        
        patterns = UserReadingPatterns(
            content_type=ContentType.PDF.value,
            average_speed_pages_per_minute=1.0,
            total_study_sessions=0
        )
        db.add(patterns)
        
        # Update existing sessions with default analytics
        print("📈 Updating existing sessions with analytics...")
        from modules.sessions.models import Session as SessionModel
        
        sessions = db.query(SessionModel).filter(
            SessionModel.status == "completed"
        ).all()
        
        for session in sessions:
            # Create session analytics if not exists
            existing_analytics = db.query(SessionAnalytics).filter(
                SessionAnalytics.session_id == session.id
            ).first()
            
            if not existing_analytics:
                analytics = SessionAnalytics(
                    session_id=session.id,
                    focus_score=session.focus_score / 100 if session.focus_score else 0.5,
                    productivity_score=session.productivity_score / 100 if session.productivity_score else 0.5,
                    pages_per_minute_actual=session.reading_speed,
                    pages_per_minute_target=1.0
                )
                db.add(analytics)
        
        # Create performance metrics for recent dates
        print("📊 Initializing performance metrics...")
        from datetime import datetime, timedelta
        
        today = datetime.utcnow()
        for i in range(7):  # Last 7 days
            date = today - timedelta(days=i)
            
            existing = db.query(PerformanceMetrics).filter(
                PerformanceMetrics.date >= datetime.combine(date.date(), datetime.min.time()),
                PerformanceMetrics.date < datetime.combine(date.date(), datetime.max.time())
            ).first()
            
            if not existing:
                metrics = PerformanceMetrics(
                    date=datetime.combine(date.date(), datetime.min.time()),
                    total_study_time_minutes=0,
                    session_count=0,
                    average_focus_score=0.5,
                    average_productivity_score=0.5,
                    average_reading_speed=1.0
                )
                db.add(metrics)
        
        db.commit()
        print("✅ Migration data created successfully")
        
        # Update existing PDFs with estimation data
        print("⏱️ Creating initial estimations for existing PDFs...")
        from modules.pdfs.models import PDF
        from modules.estimation.services import estimation_service
        
        pdfs = db.query(PDF).filter(
            PDF.processing_status == "completed"
        ).limit(10).all()  # Limit for initial migration
        
        for pdf in pdfs:
            try:
                estimation_service.estimate_pdf_completion_time(db, pdf.id)
                print(f"   ✅ Created estimation for {pdf.filename}")
            except Exception as e:
                print(f"   ⚠️ Skipped {pdf.filename}: {str(e)}")
               continue
       
       print("✅ PDF estimations created successfully")
       
       db.close()
       
   except Exception as e:
       logger.error(f"❌ Migration failed: {e}")
       print(f"❌ Migration failed: {e}")
       raise
   
   print("\n🎉 Migration to Stage 3 completed successfully!")
   print("\n🆕 New Stage 3 Features Available:")
   print("⏱️ Multi-level time estimation system")
   print("📈 Advanced session analytics engine") 
   print("🧠 AI-powered learning optimization")
   print("📊 Context-aware estimation algorithms")
   print("🎯 Performance bottleneck detection")
   print("💡 Personalized optimization suggestions")
   print("\n🚀 Start the server with: ./run_stage3.sh")


if __name__ == "__main__":
   asyncio.run(migrate_to_stage3())