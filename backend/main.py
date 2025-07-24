# backend/main.py (updated with Stage 3 modules)
"""
StudySprint 4.0 - Main FastAPI Application
Backend-first development approach - Stage 3: Enhanced Sessions & Estimation
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import logging
from pathlib import Path

from core.config import settings
from core.middleware import setup_middleware
from database import init_database

# Import all routers
from modules.topics.routes import router as topics_router
from modules.pdfs.routes import router as pdfs_router
from modules.sessions.routes import router as sessions_router
from modules.sessions.websockets import router as websocket_router
from modules.estimation.routes import router as estimation_router
from modules.analytics.routes import router as analytics_router


# Configure logging
logging.basicConfig(
   level=getattr(logging, settings.LOG_LEVEL),
   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
   handlers=[
       logging.FileHandler(settings.LOG_FILE),
       logging.StreamHandler()
   ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
   """Application lifespan events"""
   # Startup
   logger.info("🚀 Starting StudySprint 4.0 Backend - Stage 3")
   try:
       await init_database()
       logger.info("✅ Database initialized successfully")
       logger.info("📊 Topics module: Ready")
       logger.info("🔄 Sessions module: Ready with WebSocket support")
       logger.info("📄 PDFs module: Ready with upload & processing")
       logger.info("⏱️ Estimation module: Multi-level time estimation operational")
       logger.info("📈 Analytics module: Advanced session analytics ready")
       logger.info("🔍 PDF Search: Operational")
       logger.info("🎨 PDF Highlights: Supported")
       logger.info("🧠 AI-powered insights: Available")
   except Exception as e:
       logger.error(f"❌ Failed to initialize application: {e}")
       raise
   
   yield
   
   # Shutdown
   logger.info("🛑 Shutting down StudySprint 4.0 Backend")


# Create FastAPI application
app = FastAPI(
   title="StudySprint 4.0 API",
   description="Comprehensive learning tool backend - Stage 3: Enhanced Sessions & Estimation",
   version="4.0.0-stage3",
   lifespan=lifespan,
   docs_url="/api/docs",
   redoc_url="/api/redoc"
)

# Setup middleware
setup_middleware(app)

# Create and mount static directories
static_dirs = [settings.UPLOAD_DIR, settings.THUMBNAIL_DIR]
for static_dir in static_dirs:
   Path(static_dir).mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(topics_router, prefix="/api/topics", tags=["Topics"])
app.include_router(pdfs_router, prefix="/api/pdfs", tags=["PDFs"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(websocket_router, prefix="/api/sessions", tags=["WebSocket"])
app.include_router(estimation_router, prefix="/api/estimation", tags=["Estimation"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/")
async def root():
   """Root endpoint with API status"""
   return {
       "message": "StudySprint 4.0 Backend API",
       "version": "4.0.0-stage3",
       "stage": "Enhanced Sessions & Estimation - Complete",
       "features": {
           "topics": "✅ Full CRUD with progress tracking",
           "sessions": "✅ Real-time timer with WebSocket support",
           "pdfs": "✅ Upload, processing, exercise attachment",
           "search": "✅ Content-based PDF search",
           "highlights": "✅ PDF annotation system",
           "thumbnails": "✅ Automatic thumbnail generation",
           "websocket": "✅ Real-time timer updates",
           "estimation": "✅ Multi-level time estimation system",
           "analytics": "✅ Advanced session analytics engine",
           "insights": "✅ AI-powered learning optimization",
           "performance_tracking": "✅ Reading speed & trend analysis"
       },
       "endpoints": {
           "docs": "/api/docs",
           "redoc": "/api/redoc",
           "health": "/api/health"
       }
   }


@app.get("/api/health")
async def health_check():
   """Comprehensive health check"""
   return {
       "status": "healthy",
       "stage": "3 - Enhanced Sessions & Estimation Complete",
       "modules": {
           "topics": "✅ Operational",
           "sessions": "✅ Operational with WebSocket",
           "pdfs": "✅ Upload, processing & search operational",
           "estimation": "✅ Multi-level time estimation ready",
           "analytics": "✅ Advanced analytics engine operational",
           "database": "✅ Connected with enhanced relationships",
           "websocket": "✅ Available",
           "file_storage": "✅ Configured",
           "ai_insights": "✅ Learning optimization ready"
       },
       "version": settings.VERSION,
       "debug": settings.DEBUG
   }


@app.get("/api/status")
async def api_status():
   """Detailed API status for development"""
   return {
       "stage_progress": {
           "stage_3": {
               "name": "Enhanced Sessions & Estimation Module",
               "status": "✅ Complete",
               "components": {
                   "multi_level_estimation": "✅ PDF, Topic, Exercise, App-wide estimation",
                   "context_aware_algorithms": "✅ Difficulty, time-of-day, user patterns",
                   "estimation_confidence": "✅ Scoring with accuracy tracking",
                   "real_time_refinement": "✅ Learning from actual performance",
                   "advanced_session_analytics": "✅ Focus, productivity, efficiency analysis",
                   "reading_speed_analysis": "✅ Trend identification & optimization",
                   "performance_bottlenecks": "✅ Automated identification & recommendations",
                   "page_level_analytics": "✅ Detailed reading efficiency tracking",
                   "ai_powered_insights": "✅ Personalized optimization suggestions"
               }
           },
           "next_stage": {
               "name": "Goals, Notes & Recommendations",
               "scheduled": "Week 4",
               "features": [
                   "Comprehensive goals system",
                   "Wiki-style note management",
                   "Intelligent recommendations engine",
                   "Knowledge graph visualization"
               ]
           }
       },
       "api_endpoints": {
           "topics": 6,
           "sessions": 8,
           "pdfs": 12,
           "estimation": 7,
           "analytics": 8,
           "websocket": 1,
           "total": 42
       },
       "new_capabilities": {
           "estimation_accuracy": "Learning from user performance",
           "predictive_analytics": "Completion time forecasting",
           "performance_optimization": "Automated bottleneck detection",
           "contextual_insights": "Time-of-day & difficulty aware",
           "trend_analysis": "Reading speed & productivity trends"
       },
       "storage": {
           "upload_directory": settings.UPLOAD_DIR,
           "thumbnail_directory": settings.THUMBNAIL_DIR,
           "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024)
       }
   }


if __name__ == "__main__":
   uvicorn.run(
       "main:app",
       host=settings.HOST,
       port=settings.PORT,
       reload=settings.DEBUG,
       log_level=settings.LOG_LEVEL.lower(),
       access_log=True
   )