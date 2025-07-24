"""
StudySprint 4.0 - Shared Utilities
Common utility functions across modules
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate unique identifier"""
    return str(uuid.uuid4())


def generate_file_hash(file_path: Path) -> str:
    """Generate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def calculate_reading_speed(pages: int, duration_seconds: int) -> float:
    """Calculate reading speed in pages per minute"""
    if duration_seconds == 0:
        return 0.0
    minutes = duration_seconds / 60
    return pages / minutes if minutes > 0 else 0.0


def estimate_completion_time(
    total_pages: int,
    completed_pages: int,
    average_speed: float
) -> Optional[int]:
    """Estimate completion time in seconds based on progress and speed"""
    if average_speed <= 0:
        return None
    
    remaining_pages = total_pages - completed_pages
    if remaining_pages <= 0:
        return 0
    
    estimated_minutes = remaining_pages / average_speed
    return int(estimated_minutes * 60)


def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension"""
    file_extension = Path(filename).suffix.lower()
    return file_extension in [f".{ext}" if not ext.startswith(".") else ext 
                             for ext in allowed_types]


def safe_filename(filename: str) -> str:
    """Generate safe filename for storage"""
    # Remove dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    safe_name = "".join(c for c in filename if c in safe_chars)
    
    # Ensure it's not empty and add timestamp
    if not safe_name:
        safe_name = "file"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_part = Path(safe_name).stem[:50]  # Limit length
    extension = Path(safe_name).suffix
    
    return f"{name_part}_{timestamp}{extension}"


def paginate_response(
    items: List[Any],
    total: int,
    page: int,
    size: int
) -> Dict[str, Any]:
    """Create paginated response format"""
    total_pages = (total + size - 1) // size  # Ceiling division
    
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


class TimeTracker:
    """Utility class for tracking time intervals"""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.total_seconds: int = 0
        self.is_running: bool = False
    
    def start(self):
        """Start time tracking"""
        if not self.is_running:
            self.start_time = datetime.utcnow()
            self.is_running = True
    
    def pause(self):
        """Pause time tracking"""
        if self.is_running and self.start_time:
            elapsed = datetime.utcnow() - self.start_time
            self.total_seconds += int(elapsed.total_seconds())
            self.is_running = False
    
    def resume(self):
        """Resume time tracking"""
        if not self.is_running:
            self.start_time = datetime.utcnow()
            self.is_running = True
    
    def stop(self) -> int:
        """Stop tracking and return total seconds"""
        if self.is_running:
            self.pause()
        return self.total_seconds
    
    def get_current_total(self) -> int:
        """Get current total including active time"""
        total = self.total_seconds
        if self.is_running and self.start_time:
            elapsed = datetime.utcnow() - self.start_time
            total += int(elapsed.total_seconds())
        return total
