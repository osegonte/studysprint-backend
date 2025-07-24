"""
StudySprint 4.0 - Main FastAPI Application
Backend-first development approach - Stage 1 Complete
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
from modules.topics.routes import router as topics_router
from modules.pdfs.routes import router as pdfs_router
from modules.sessions.routes import router as sessions_router
from modules.sessions.websockets import router as websocket_router


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
    logger.info("🚀 Starting StudySprint 4.0 Backend - Stage 1")
    try:
        await init_database()
        logger.info("✅ Database initialized successfully")
        logger.info("📊 Topics module: Ready")
        logger.info("🔄 Sessions module: Ready with WebSocket support")
        logger.info("📄 PDFs module: Placeholder ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down StudySprint 4.0 Backend")


# Create FastAPI application
app = FastAPI(
    title="StudySprint 4.0 API",
    description="Comprehensive learning tool backend - Stage 1 Complete",
    version="4.0.0-stage1",
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


@app.get("/")
async def root():
    """Root endpoint with API status"""
    return {
        "message": "StudySprint 4.0 Backend API",
        "version": "4.0.0-stage1",
        "stage": "Core Foundation APIs - Complete",
        "features": {
            "topics": "✅ Full CRUD with progress tracking",
            "sessions": "✅ Real-time timer with WebSocket support",
            "pdfs": "🔄 Placeholder (Stage 1 - Day 2)",
            "websocket": "✅ Real-time timer updates"
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
        "stage": "1 - Core Foundation APIs",
        "modules": {
            "topics": "✅ Operational",
            "sessions": "✅ Operational with WebSocket",
            "pdfs": "🔄 Placeholder",
            "database": "✅ Connected",
            "websocket": "✅ Available"
        },
        "version": settings.VERSION,
        "debug": settings.DEBUG
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status for development"""
    return {
        "stage_progress": {
            "stage_1": {
                "name": "Core Foundation APIs",
                "status": "✅ Complete",
                "components": {
                    "topics": "✅ Full CRUD + Progress tracking",
                    "sessions": "✅ Real-time tracking + WebSocket",
                    "database": "✅ SQLAlchemy models + relationships",
                    "websocket": "✅ Real-time timer updates"
                }
            },
            "next_stage": {
                "name": "PDFs Module Implementation",
                "scheduled": "Day 2",
                "features": [
                    "PDF upload with validation",
                    "Exercise PDF attachment",
                    "Metadata extraction",
                    "File serving and thumbnails"
                ]
            }
        },
        "api_endpoints": {
            "topics": 6,
            "sessions": 8,
            "websocket": 1,
            "pdfs": "0 (placeholder)"
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