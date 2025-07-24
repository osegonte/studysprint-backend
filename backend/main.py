"""
StudySprint 4.0 - Main FastAPI Application
Backend-first development approach - Stage 1
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
from shared.database import init_database
from modules.topics.routes import router as topics_router
from modules.pdfs.routes import router as pdfs_router
from modules.sessions.routes import router as sessions_router
from modules.sessions.websockets import router as websocket_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting StudySprint 4.0 Backend")
    await init_database()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down StudySprint 4.0 Backend")


# Create FastAPI application
app = FastAPI(
    title="StudySprint 4.0 API",
    description="Comprehensive learning tool backend - Stage 1",
    version="4.0.0-stage1",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup middleware
setup_middleware(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(topics_router, prefix="/api/topics", tags=["Topics"])
app.include_router(pdfs_router, prefix="/api/pdfs", tags=["PDFs"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(websocket_router, prefix="/api/sessions", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StudySprint 4.0 Backend API",
        "version": "4.0.0-stage1",
        "stage": "Core Foundation APIs",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "stage": "1",
        "modules": ["topics", "pdfs", "sessions"]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
