# WebSocket Real-Time Notifications

This document describes the WebSocket implementation for real-time notifications in the Cybersecurity Awareness Platform.

## Overview

The WebSocket implementation provides real-time, bidirectional communication between the server and clients, enabling instant notifications for various events such as:

- Quiz completion results
- Certificate generation
- Course updates
- Phishing campaign results
- System maintenance announcements

## Architecture

### Backend Components

1. **NotificationService** (`backend/services/notification_service.py`)
   - Manages notification creation and delivery
   - Provides specialized notification methods for different event types
   - Handles message formatting and severity levels

2. **ConnectionManager** (`backend/services/notification_service.py`)
   - Manages WebSocket connections for multiple users
   - Handles connection lifecycle (connect, disconnect, reconnect)
   - Stores pending messages for offline users
   - Implements message broadcasting and targeted delivery

3. **WebSocket Route** (`backend/api/routes/notifications.py`)
   - Provides the WebSocket endpoint at `/api/v1/notifications/ws`
   - Handles authentication via JWT tokens
   - Implements ping/pong for connection health checks
   - Provides REST endpoints for testing and status monitoring

### Frontend Components

1. **useWebSocket Hook** (`frontend/src/hooks/useWebSocket.ts`)
   - React hook for WebSocket connection management
   - Automatic reconnection with exponential backoff
   - Message handling and state management
   - Connection status monitoring

2. **NotificationCenter Component** (`frontend/src/components/Notifications/NotificationCenter.tsx`)
   - UI component for displaying notifications
   - Real-time notification badges
   - Mark as read functionality
   - Connection status indicator

## API Endpoints

### WebSocket Endpoint

```
ws://localhost:8000/api/v1/notifications/ws?token=YOUR_JWT_TOKEN
```

Authentication is required via JWT token passed as query parameter.

### REST Endpoints

#### Get Connection Status
```http
GET /api/v1/notifications/status
Authorization: Bearer YOUR_JWT_TOKEN
```

Response:
```json
{
  "total_connections": 5,
  "connections_per_user": {
    "user123": 2,
    "user456": 3
  },
  "user_connected": true
}
```

#### Send Test Notification
```http
POST /api/v1/notifications/test
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "notification_type": "test",
  "title": "Test Notification",
  "message": "This is a test",
  "severity": "info"
}
```

## Message Format

### Notification Message Structure
```typescript
interface NotificationMessage {
  id: string;
  type: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  data?: Record<string, any>;
  timestamp: string;
  read: boolean;
}
```

### Message Types

1. **connection** - Initial connection confirmation
2. **course_update** - Course content updates
3. **quiz_result** - Quiz completion results
4. **certificate_ready** - Certificate generation complete
5. **phishing_result** - Phishing test results
6. **system_maintenance** - System maintenance announcements

## Frontend Integration

### Basic Usage

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function MyComponent() {
  const { 
    isConnected, 
    notifications, 
    unreadCount,
    markAsRead 
  } = useWebSocket({
    onMessage: (notification) => {
      console.log('New notification:', notification);
    }
  });

  return (
    <div>
      {isConnected ? 'Connected' : 'Disconnected'}
      <span>Unread: {unreadCount}</span>
    </div>
  );
}
```

### Adding to Layout

The NotificationCenter component is already integrated into the main Navbar:

```typescript
import { NotificationCenter } from '../Notifications';

export const Navbar = () => {
  return (
    <nav>
      {/* Other navbar items */}
      <NotificationCenter />
    </nav>
  );
};
```

## Service Integration

### Example: Quiz Service Integration

```python
from services.notification_service import notification_service

async def submit_quiz(self, user_id: int, quiz_id: int, answers: Dict):
    # ... quiz processing logic ...
    
    # Send notification about quiz result
    await notification_service.notify_quiz_result(
        user_id=str(user_id),
        quiz_id=str(quiz_id),
        score=percentage
    )
    
    # If certificate was generated
    if certificate_id:
        await notification_service.notify_certificate_ready(
            user_id=str(user_id),
            course_id=str(quiz.course_id),
            certificate_id=str(certificate_id)
        )
```

## Testing

### Backend Testing

Run the test script to verify WebSocket functionality:

```bash
cd backend
python test_websocket.py
```

### Frontend Testing

1. Navigate to `/notification-test` when logged in
2. Use the test interface to send different notification types
3. Verify notifications appear in real-time in the notification center

### Manual Testing with WebSocket Client

```bash
# Install websocat
brew install websocat  # macOS
# or
cargo install websocat  # with Rust

# Connect to WebSocket
websocat "ws://localhost:8000/api/v1/notifications/ws?token=YOUR_JWT_TOKEN"

# Send ping
{"type": "ping"}
```

## Configuration

### Backend Configuration

No additional configuration is required. The WebSocket functionality uses the existing FastAPI server.

### Frontend Configuration

The WebSocket URL is automatically constructed based on the current window location. For production deployments with HTTPS, it will automatically use `wss://` protocol.

### Nginx Configuration for Production

Add WebSocket support to your Nginx configuration:

```nginx
location /api/v1/notifications/ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Security Considerations

1. **Authentication**: All WebSocket connections require valid JWT tokens
2. **Authorization**: Notifications are only sent to authorized users
3. **Message Validation**: All messages are validated using Pydantic models
4. **Connection Limits**: Consider implementing per-user connection limits in production
5. **Rate Limiting**: The notification test endpoint should be rate-limited

## Performance Considerations

1. **Connection Pooling**: The ConnectionManager maintains a pool of active connections
2. **Message Queuing**: Pending messages are stored for offline users (up to 7 days)
3. **Heartbeat**: Ping/pong messages every 30 seconds to detect stale connections
4. **Auto-reconnection**: Frontend automatically reconnects with exponential backoff
5. **Resource Cleanup**: Periodic cleanup task removes old pending messages

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure backend server is running
   - Check if the WebSocket endpoint is accessible
   - Verify JWT token is valid

2. **Authentication Failed**
   - Token may be expired
   - Ensure token is passed correctly in query parameter

3. **Messages Not Received**
   - Check browser console for WebSocket errors
   - Verify notification service is called in backend
   - Check connection status in notification center

### Debug Mode

Enable debug logging in the backend:

```python
# In backend/core/logging.py
logger.setLevel("DEBUG")
```

Monitor WebSocket connections:
```bash
# Watch active connections
watch 'curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/notifications/status'
```

## Future Enhancements

1. **Message Persistence**: Store notifications in database for history
2. **Topics/Channels**: Subscribe to specific notification types
3. **Delivery Confirmation**: Track when notifications are received/read
4. **Batch Notifications**: Group similar notifications
5. **Push Notifications**: Integrate with browser push API
6. **Mobile Support**: Native mobile app WebSocket integration