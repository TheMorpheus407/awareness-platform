"""WebSocket route for real-time notifications."""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import jwt

from core.config import settings
from db.session import get_db
from models.user import User
from services.notification_service import notification_manager, notification_service
from api.dependencies.auth import get_current_user


router = APIRouter()
security = HTTPBearer()


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from WebSocket connection.
    Token can be passed as query parameter or in Authorization header.
    """
    if not token:
        # Try to get from headers
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Get user from database
        user = await db.get(User, user_id)
        return user
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token in WebSocket connection")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token in WebSocket connection")
        return None
    except Exception as e:
        logger.error(f"Error authenticating WebSocket user: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.
    
    Connect using: ws://localhost:8000/api/v1/notifications/ws?token=YOUR_JWT_TOKEN
    """
    # Authenticate user
    user = await get_current_user_ws(websocket, token, db)
    
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    user_id = str(user.id)
    
    try:
        # Accept connection and register with manager
        await notification_manager.connect(websocket, user_id)
        
        # Send welcome message
        await notification_service.notify_user(
            user_id=user_id,
            notification_type="connection",
            title="Connected",
            message="You are now connected to real-time notifications",
            severity="success"
        )
        
        # Keep connection alive
        while True:
            # Wait for messages from client (heartbeat, etc.)
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "mark_read":
                # Handle marking notifications as read
                notification_id = data.get("notification_id")
                # TODO: Implement marking notifications as read in database
                logger.info(f"User {user_id} marked notification {notification_id} as read")
            
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        notification_manager.disconnect(websocket, user_id)
        await websocket.close(code=1011, reason="Internal server error")


@router.get("/status")
async def get_websocket_status(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket connection status and statistics."""
    connection_count = notification_manager.get_connection_count()
    total_connections = notification_manager.get_total_connections()
    
    return {
        "total_connections": total_connections,
        "connections_per_user": connection_count,
        "user_connected": str(current_user.id) in connection_count
    }


@router.post("/test")
async def test_notification(
    notification_type: str = "test",
    title: str = "Test Notification",
    message: str = "This is a test notification",
    severity: str = "info",
    current_user: User = Depends(get_current_user)
):
    """Send a test notification to the current user."""
    notification = await notification_service.notify_user(
        user_id=str(current_user.id),
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity
    )
    
    return {
        "message": "Notification sent",
        "notification": notification
    }