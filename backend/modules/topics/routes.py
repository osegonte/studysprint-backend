"""
StudySprint 4.0 - Topics API Routes
REST API endpoints for topics management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from .schemas import TopicCreate, TopicUpdate, TopicResponse, TopicProgress, TopicListResponse
from .services import topics_service
from shared.utils import paginate_response

router = APIRouter()


@router.post("/", response_model=TopicResponse, status_code=201)
async def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db)
):
    """Create a new topic"""
    topic = topics_service.create_topic(db, topic_data)
    return topic


@router.get("/", response_model=TopicListResponse)
async def get_topics(
    skip: int = Query(0, ge=0, description="Number of topics to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of topics to return"),
    active_only: bool = Query(True, description="Return only active topics"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search topics by name"),
    db: Session = Depends(get_db)
):
    """Get topics with filtering and pagination"""
    topics, total = topics_service.get_topics(
        db, skip=skip, limit=limit, active_only=active_only, 
        priority=priority, search=search
    )
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    
    return TopicListResponse(
        items=topics,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        total_pages=total_pages
    )


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """Get topic by ID"""
    topic = topics_service.get_topic_by_id(db, topic_id)
    return topic


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db)
):
    """Update topic"""
    topic = topics_service.update_topic(db, topic_id, topic_data)
    return topic


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """Delete (archive) topic"""
    success = topics_service.delete_topic(db, topic_id)
    return {"success": success, "message": "Topic archived successfully"}


@router.get("/{topic_id}/progress", response_model=TopicProgress)
async def get_topic_progress(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed progress analytics for a topic"""
    progress = topics_service.get_topic_progress(db, topic_id)
    return progress


@router.patch("/{topic_id}/progress")
async def update_topic_progress(
    topic_id: int,
    completed_pages: int = Query(..., ge=0, description="Number of completed pages"),
    db: Session = Depends(get_db)
):
    """Update topic progress"""
    topic = topics_service.update_progress(db, topic_id, completed_pages)
    return {
        "success": True,
        "message": f"Progress updated to {topic.completion_percentage}%",
        "topic": topic
    }