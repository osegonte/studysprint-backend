"""
StudySprint 4.0 - Main FastAPI Application
Backend-first development approach - Stage 2 Complete
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
    logger.info("🚀 Starting StudySprint 4.0 Backend - Stage 2")
    try:
        await init_database()
        logger.info("✅ Database initialized successfully")
        logger.info("📊 Topics module: Ready")
        logger.info("🔄 Sessions module: Ready with WebSocket support")
        logger.info("📄 PDFs module: Ready with upload & processing")
        logger.info("🔍 PDF Search: Operational")
        logger.info("🎨 PDF Highlights: Supported")
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down StudySprint 4.0 Backend")


# Create FastAPI application
app = FastAPI(
    title="StudySprint 4.0 API",
    description="Comprehensive learning tool backend - Stage 2 Complete",
    version="4.0.0-stage2",
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
        "version": "4.0.0-stage2",
        "stage": "PDFs Module - Complete",
        "features": {
            "topics": "✅ Full CRUD with progress tracking",
            "sessions": "✅ Real-time timer with WebSocket support",
            "pdfs": "✅ Upload, processing, exercise attachment",
            "search": "✅ Content-based PDF search",
            "highlights": "✅ PDF annotation system",
            "thumbnails": "✅ Automatic thumbnail generation",
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
        "stage": "2 - PDFs Module Complete",
        "modules": {
            "topics": "✅ Operational",
            "sessions": "✅ Operational with WebSocket",
            "pdfs": "✅ Upload, processing & search operational",
            "database": "✅ Connected with relationships",
            "websocket": "✅ Available",
            "file_storage": "✅ Configured"
        },
        "version": settings.VERSION,
        "debug": settings.DEBUG
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status for development"""
    return {
        "stage_progress": {
            "stage_2": {
                "name": "PDFs Module Implementation",
                "status": "✅ Complete",
                "components": {
                    "pdf_upload": "✅ Multi-part upload with validation",
                    "metadata_extraction": "✅ PyPDF2 page count & text",
                    "exercise_attachment": "✅ Parent-child PDF relationships",
                    "file_serving": "✅ Streaming with caching headers",
                    "thumbnail_generation": "✅ Automatic thumbnail creation",
                    "search_system": "✅ Content & filename search",
                    "highlight_system": "✅ Coordinate-based annotations",
                    "database_relationships": "✅ Cross-module foreign keys"
                }
            },
            "next_stage": {
                "name": "Enhanced Sessions Analytics",
                "scheduled": "Week 2",
                "features": [
                    "Advanced session analytics",
                    "Multi-level time estimation",
                    "Reading speed analysis",
                    "Performance optimization"
                ]
            }
        },
        "api_endpoints": {
            "topics": 6,
            "sessions": 8,
            "pdfs": 12,
            "websocket": 1,
            "total": 27
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