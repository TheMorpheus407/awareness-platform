"""Real-time notification service using WebSockets."""

import json
import asyncio
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel, Field


class NotificationMessage(BaseModel):
    """Notification message model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    title: str
    message: str
    severity: str = "info"  # info, warning, error, success
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False


class ConnectionManager:
    """WebSocket connection manager for handling multiple clients."""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store pending messages for offline users
        self.pending_messages: Dict[str, List[NotificationMessage]] = {}
        # Background task for cleanup
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
        
        # Send any pending messages
        await self._send_pending_messages(user_id, websocket)
        
        # Start cleanup task if not running
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Remove user entry if no connections remain
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
            logger.info(f"User {user_id} disconnected. Remaining connections: {len(self.active_connections.get(user_id, []))}")
    
    async def send_personal_message(self, message: NotificationMessage, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            # User is online, send to all their connections
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message.dict())
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected websockets
            for conn in disconnected:
                self.disconnect(conn, user_id)
        else:
            # User is offline, store message
            if user_id not in self.pending_messages:
                self.pending_messages[user_id] = []
            
            self.pending_messages[user_id].append(message)
            logger.info(f"Stored pending message for offline user {user_id}")
    
    async def broadcast(self, message: NotificationMessage, exclude_users: Optional[Set[str]] = None):
        """Broadcast a message to all connected users."""
        exclude_users = exclude_users or set()
        disconnected = []
        
        for user_id, connections in self.active_connections.items():
            if user_id in exclude_users:
                continue
                
            for connection in connections:
                try:
                    await connection.send_json(message.dict())
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.append((connection, user_id))
        
        # Clean up disconnected websockets
        for conn, user_id in disconnected:
            self.disconnect(conn, user_id)
    
    async def send_to_group(self, message: NotificationMessage, user_ids: List[str]):
        """Send a message to a specific group of users."""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def _send_pending_messages(self, user_id: str, websocket: WebSocket):
        """Send all pending messages to a newly connected user."""
        if user_id in self.pending_messages:
            messages = self.pending_messages.pop(user_id, [])
            
            for message in messages:
                try:
                    await websocket.send_json(message.dict())
                except Exception as e:
                    logger.error(f"Error sending pending message to user {user_id}: {e}")
                    # Re-add message to pending if send fails
                    if user_id not in self.pending_messages:
                        self.pending_messages[user_id] = []
                    self.pending_messages[user_id].append(message)
                    break
    
    async def _periodic_cleanup(self):
        """Periodically clean up old pending messages."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Remove messages older than 7 days
                cutoff_time = datetime.utcnow().timestamp() - (7 * 24 * 3600)
                
                for user_id in list(self.pending_messages.keys()):
                    messages = self.pending_messages.get(user_id, [])
                    self.pending_messages[user_id] = [
                        msg for msg in messages 
                        if msg.timestamp.timestamp() > cutoff_time
                    ]
                    
                    # Remove user if no messages remain
                    if not self.pending_messages[user_id]:
                        del self.pending_messages[user_id]
                
                logger.info("Completed periodic cleanup of pending messages")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def get_connection_count(self) -> Dict[str, int]:
        """Get the number of connections per user."""
        return {
            user_id: len(connections) 
            for user_id, connections in self.active_connections.items()
        }
    
    def get_total_connections(self) -> int:
        """Get the total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
notification_manager = ConnectionManager()


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        self.manager = notification_manager
    
    async def notify_user(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> NotificationMessage:
        """Send a notification to a specific user."""
        notification = NotificationMessage(
            type=notification_type,
            title=title,
            message=message,
            severity=severity,
            data=data
        )
        
        await self.manager.send_personal_message(notification, user_id)
        return notification
    
    async def notify_group(
        self,
        user_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> NotificationMessage:
        """Send a notification to a group of users."""
        notification = NotificationMessage(
            type=notification_type,
            title=title,
            message=message,
            severity=severity,
            data=data
        )
        
        await self.manager.send_to_group(notification, user_ids)
        return notification
    
    async def broadcast_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
        exclude_users: Optional[Set[str]] = None
    ) -> NotificationMessage:
        """Broadcast a notification to all connected users."""
        notification = NotificationMessage(
            type=notification_type,
            title=title,
            message=message,
            severity=severity,
            data=data
        )
        
        await self.manager.broadcast(notification, exclude_users)
        return notification
    
    async def notify_course_update(self, course_id: str, user_ids: List[str], update_type: str):
        """Notify users about course updates."""
        return await self.notify_group(
            user_ids=user_ids,
            notification_type="course_update",
            title="Course Update",
            message=f"There's a new update for your course",
            data={"course_id": course_id, "update_type": update_type}
        )
    
    async def notify_quiz_result(self, user_id: str, quiz_id: str, score: float):
        """Notify user about quiz results."""
        return await self.notify_user(
            user_id=user_id,
            notification_type="quiz_result",
            title="Quiz Completed",
            message=f"Your quiz score: {score:.1f}%",
            severity="success" if score >= 70 else "warning",
            data={"quiz_id": quiz_id, "score": score}
        )
    
    async def notify_certificate_ready(self, user_id: str, course_id: str, certificate_id: str):
        """Notify user that their certificate is ready."""
        return await self.notify_user(
            user_id=user_id,
            notification_type="certificate_ready",
            title="Certificate Ready!",
            message="Your course certificate is now available for download",
            severity="success",
            data={"course_id": course_id, "certificate_id": certificate_id}
        )
    
    async def notify_phishing_campaign_result(self, user_id: str, campaign_id: str, clicked: bool):
        """Notify user about phishing campaign results."""
        return await self.notify_user(
            user_id=user_id,
            notification_type="phishing_result",
            title="Phishing Test Result",
            message="You clicked on a simulated phishing email" if clicked else "Good job avoiding the phishing email!",
            severity="warning" if clicked else "success",
            data={"campaign_id": campaign_id, "clicked": clicked}
        )
    
    async def notify_system_maintenance(self, message: str, maintenance_time: datetime):
        """Notify all users about system maintenance."""
        return await self.broadcast_notification(
            notification_type="system_maintenance",
            title="Scheduled Maintenance",
            message=message,
            severity="warning",
            data={"maintenance_time": maintenance_time.isoformat()}
        )


# Global notification service instance
notification_service = NotificationService()