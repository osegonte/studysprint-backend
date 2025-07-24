"""
StudySprint 4.0 - Configuration Settings
Environment configuration for development and production
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "StudySprint 4.0"
    VERSION: str = "4.0.0-stage1"
    DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Database
    DATABASE_PATH: str = "data/studysprint.db"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    
    # File Upload
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf"]
    UPLOAD_DIR: str = "static/uploads"
    THUMBNAIL_DIR: str = "static/thumbnails"
    
    # Session Settings
    SESSION_TIMEOUT: int = 3600  # 1 hour
    WEBSOCKET_TIMEOUT: int = 300  # 5 minutes
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/studysprint.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Ensure required directories exist
def ensure_directories():
    """Create required directories if they don't exist"""
    dirs = [
        Path(settings.DATABASE_PATH).parent,
        Path(settings.UPLOAD_DIR),
        Path(settings.THUMBNAIL_DIR),
        Path(settings.LOG_FILE).parent,
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


# Initialize directories
ensure_directories()
