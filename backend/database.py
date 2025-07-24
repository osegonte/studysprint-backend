"""
StudySprint 4.0 - Database Configuration
SQLite setup with connection pooling and migrations
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = f"sqlite:///{settings.DATABASE_PATH}"

# SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_database():
    """Initialize database and create tables"""
    try:
        # Ensure database directory exists
        Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def reset_database():
    """Reset database - drop and recreate all tables"""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database reset successfully")
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise
