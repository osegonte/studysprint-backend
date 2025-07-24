"""
StudySprint 4.0 - WebSocket Implementation
Real-time timer and session updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
import asyncio
import json
import logging
from datetime import datetime

from database import get_db
from .services import sessions_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: int):
        """Accept WebSocket connection"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"🔌 WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: int):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"🔌 WebSocket disconnected for session {session_id}")
    
    async def send_personal_message(self, message: dict, session_id: int):
        """Send message to all connections for a session"""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove broken connections
                    await self.cleanup_connection(connection, session_id)
    
    async def cleanup_connection(self, websocket: WebSocket, session_id: int):
        """Clean up broken connections"""
        try:
            self.disconnect(websocket, session_id)
        except:
            pass


manager = ConnectionManager()


@router.websocket("/{session_id}/timer")
async def websocket_timer(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time timer updates"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Send timer update every second
            timer_state = sessions_service.get_current_timer_state(session_id)
            
            update_message = {
                "type": "timer_update",
                "session_id": session_id,
                "elapsed_seconds": timer_state["elapsed_seconds"],
                "is_running": timer_state["is_running"],
                "current_time": datetime.utcnow().isoformat(),
                "formatted_time": format_timer_display(timer_state["elapsed_seconds"])
            }
            
            await manager.send_personal_message(update_message, session_id)
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {e}")
        manager.disconnect(websocket, session_id)


def format_timer_display(seconds: int) -> str:
    """Format seconds for timer display (HH:MM:SS)"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# WebSocket event handlers
async def broadcast_session_update(session_id: int, event_type: str, data: dict):
    """Broadcast session updates to connected clients"""
    message = {
        "type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    await manager.send_personal_message(message, session_id)