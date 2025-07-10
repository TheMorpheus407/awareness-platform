"""Real-time analytics service for live dashboard updates."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis
from fastapi import WebSocket

from models.analytics import AnalyticsEvent
from models.user import User
from models.company import Company
from core.cache import cache, cache_key
from core.logging import logger
from core.config import settings


class RealTimeAnalyticsService:
    """Service for real-time analytics and WebSocket updates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
        self.redis_pubsub = None
        self._subscription_task = None
        
    async def initialize(self):
        """Initialize Redis pub/sub for real-time updates."""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            self.redis_pubsub = self.redis_client.pubsub()
            await self.redis_pubsub.subscribe("analytics:*")
            
            # Start subscription handler
            self._subscription_task = asyncio.create_task(self._handle_subscriptions())
            logger.info("Real-time analytics service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize real-time analytics: {e}")
            
    async def shutdown(self):
        """Cleanup resources."""
        if self._subscription_task:
            self._subscription_task.cancel()
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe()
            await self.redis_pubsub.close()
        if hasattr(self, 'redis_client'):
            await self.redis_client.close()
            
    async def connect(self, websocket: WebSocket, company_id: int):
        """Connect a WebSocket client for real-time updates."""
        await websocket.accept()
        self.active_connections[company_id].add(websocket)
        
        # Send initial data
        await self.send_initial_data(websocket, company_id)
        
    async def disconnect(self, websocket: WebSocket, company_id: int):
        """Disconnect a WebSocket client."""
        self.active_connections[company_id].discard(websocket)
        if not self.active_connections[company_id]:
            del self.active_connections[company_id]
            
    async def send_initial_data(self, websocket: WebSocket, company_id: int):
        """Send initial dashboard data to new WebSocket connection."""
        try:
            # Get cached dashboard data
            cache_key_str = cache_key("realtime", "dashboard", company_id)
            dashboard_data = await cache.get(cache_key_str)
            
            if not dashboard_data:
                # Generate fresh data if not cached
                dashboard_data = await self._generate_dashboard_snapshot(company_id)
                await cache.set(cache_key_str, dashboard_data, expire=60)
                
            await websocket.send_json({
                "type": "initial_data",
                "data": dashboard_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            
    async def broadcast_to_company(self, company_id: int, message: dict):
        """Broadcast message to all connected clients of a company."""
        if company_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[company_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.add(websocket)
                    
            # Remove disconnected clients
            for ws in disconnected:
                self.active_connections[company_id].discard(ws)
                
    async def track_event(self, event: AnalyticsEvent):
        """Track an analytics event and broadcast updates."""
        try:
            # Store event
            self.db.add(event)
            await self.db.flush()
            
            # Publish to Redis for other instances
            channel = f"analytics:{event.company_id}"
            await self.redis_client.publish(channel, json.dumps({
                "event_type": event.event_type,
                "event_category": event.event_category,
                "user_id": event.user_id,
                "event_data": event.event_data,
                "timestamp": event.created_at.isoformat()
            }))
            
            # Update real-time metrics
            await self._update_real_time_metrics(event)
            
        except Exception as e:
            logger.error(f"Error tracking real-time event: {e}")
            
    async def _handle_subscriptions(self):
        """Handle Redis pub/sub messages."""
        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    if channel.startswith("analytics:"):
                        company_id = int(channel.split(":")[1])
                        data = json.loads(message["data"])
                        
                        # Broadcast to connected clients
                        await self.broadcast_to_company(company_id, {
                            "type": "event_update",
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
        except asyncio.CancelledError:
            logger.info("Subscription handler cancelled")
        except Exception as e:
            logger.error(f"Error in subscription handler: {e}")
            
    async def _update_real_time_metrics(self, event: AnalyticsEvent):
        """Update real-time metrics based on event."""
        company_id = event.company_id
        if not company_id:
            return
            
        # Update different metrics based on event type
        update_data = {}
        
        if event.event_type == AnalyticsEvent.EventType.LOGIN:
            update_data["active_users"] = await self._get_active_users_count(company_id)
            
        elif event.event_type == AnalyticsEvent.EventType.COURSE_COMPLETED:
            update_data["courses_completed_today"] = await self._get_courses_completed_today(company_id)
            
        elif event.event_type in [
            AnalyticsEvent.EventType.PHISHING_LINK_CLICKED,
            AnalyticsEvent.EventType.PHISHING_REPORTED
        ]:
            update_data["phishing_metrics"] = await self._get_phishing_metrics_today(company_id)
            
        if update_data:
            await self.broadcast_to_company(company_id, {
                "type": "metric_update",
                "data": update_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    async def _generate_dashboard_snapshot(self, company_id: int) -> Dict[str, Any]:
        """Generate current dashboard snapshot."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "active_users": await self._get_active_users_count(company_id),
            "courses_completed_today": await self._get_courses_completed_today(company_id),
            "phishing_metrics": await self._get_phishing_metrics_today(company_id),
            "recent_events": await self._get_recent_events(company_id, limit=10),
            "online_users": len(self.active_connections.get(company_id, set())),
        }
        
    async def _get_active_users_count(self, company_id: int) -> int:
        """Get count of active users in last 15 minutes."""
        since = datetime.utcnow() - timedelta(minutes=15)
        
        query = select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
            and_(
                AnalyticsEvent.company_id == company_id,
                AnalyticsEvent.created_at >= since,
                AnalyticsEvent.event_type == AnalyticsEvent.EventType.LOGIN
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
        
    async def _get_courses_completed_today(self, company_id: int) -> int:
        """Get count of courses completed today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = select(func.count(AnalyticsEvent.id)).where(
            and_(
                AnalyticsEvent.company_id == company_id,
                AnalyticsEvent.created_at >= today_start,
                AnalyticsEvent.event_type == AnalyticsEvent.EventType.COURSE_COMPLETED
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
        
    async def _get_phishing_metrics_today(self, company_id: int) -> Dict[str, int]:
        """Get phishing metrics for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count different phishing events
        metrics = {}
        
        for event_type, metric_name in [
            (AnalyticsEvent.EventType.PHISHING_EMAIL_SENT, "sent"),
            (AnalyticsEvent.EventType.PHISHING_EMAIL_OPENED, "opened"),
            (AnalyticsEvent.EventType.PHISHING_LINK_CLICKED, "clicked"),
            (AnalyticsEvent.EventType.PHISHING_REPORTED, "reported"),
        ]:
            query = select(func.count(AnalyticsEvent.id)).where(
                and_(
                    AnalyticsEvent.company_id == company_id,
                    AnalyticsEvent.created_at >= today_start,
                    AnalyticsEvent.event_type == event_type
                )
            )
            result = await self.db.execute(query)
            metrics[metric_name] = result.scalar() or 0
            
        return metrics
        
    async def _get_recent_events(self, company_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events for activity feed."""
        query = select(AnalyticsEvent).where(
            AnalyticsEvent.company_id == company_id
        ).order_by(
            AnalyticsEvent.created_at.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        return [
            {
                "id": event.id,
                "type": event.event_type,
                "category": event.event_category,
                "user_id": event.user_id,
                "data": event.event_data,
                "timestamp": event.created_at.isoformat()
            }
            for event in events
        ]
        
    async def get_live_metrics(self, company_id: int) -> Dict[str, Any]:
        """Get live metrics for dashboard."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": await self._generate_dashboard_snapshot(company_id),
            "trends": await self._calculate_live_trends(company_id)
        }
        
    async def _calculate_live_trends(self, company_id: int) -> Dict[str, Any]:
        """Calculate live trend indicators."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        trends = {}
        
        # Login trend
        current_logins = await self._count_events(
            company_id, AnalyticsEvent.EventType.LOGIN, hour_ago, now
        )
        previous_logins = await self._count_events(
            company_id, AnalyticsEvent.EventType.LOGIN, 
            hour_ago - timedelta(hours=1), hour_ago
        )
        trends["login_trend"] = self._calculate_trend(current_logins, previous_logins)
        
        # Course completion trend
        current_completions = await self._count_events(
            company_id, AnalyticsEvent.EventType.COURSE_COMPLETED, day_ago, now
        )
        previous_completions = await self._count_events(
            company_id, AnalyticsEvent.EventType.COURSE_COMPLETED,
            day_ago - timedelta(days=1), day_ago
        )
        trends["completion_trend"] = self._calculate_trend(
            current_completions, previous_completions
        )
        
        return trends
        
    async def _count_events(
        self, 
        company_id: int, 
        event_type: str, 
        start: datetime, 
        end: datetime
    ) -> int:
        """Count events in a time range."""
        query = select(func.count(AnalyticsEvent.id)).where(
            and_(
                AnalyticsEvent.company_id == company_id,
                AnalyticsEvent.event_type == event_type,
                AnalyticsEvent.created_at.between(start, end)
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
        
    def _calculate_trend(self, current: int, previous: int) -> Dict[str, Any]:
        """Calculate trend from two values."""
        if previous == 0:
            change_percent = 100 if current > 0 else 0
        else:
            change_percent = ((current - previous) / previous) * 100
            
        return {
            "current": current,
            "previous": previous,
            "change": current - previous,
            "change_percent": round(change_percent, 2),
            "direction": "up" if current > previous else "down" if current < previous else "stable"
        }