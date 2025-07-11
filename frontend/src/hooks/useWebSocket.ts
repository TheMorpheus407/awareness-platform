import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './useAuth';
import toast from 'react-hot-toast';

export interface NotificationMessage {
  id: string;
  type: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  data?: Record<string, any>;
  timestamp: string;
  read: boolean;
}

interface UseWebSocketOptions {
  onMessage?: (message: NotificationMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
  } = options;

  const { user, token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<NotificationMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isIntentionalDisconnectRef = useRef(false);

  const getWebSocketUrl = useCallback(() => {
    if (!token) return null;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/v1/notifications/ws?token=${token}`;
  }, [token]);

  const connect = useCallback(() => {
    if (!user || !token) {
      console.log('Cannot connect WebSocket: No user or token');
      return;
    }

    const wsUrl = getWebSocketUrl();
    if (!wsUrl) return;

    try {
      // Clean up existing connection
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        isIntentionalDisconnectRef.current = true;
        wsRef.current.close();
      }

      console.log('Connecting to WebSocket...');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        isIntentionalDisconnectRef.current = false;
        
        // Send initial ping
        ws.send(JSON.stringify({ type: 'ping' }));
        
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            // Handle pong response
            return;
          }

          // Add notification to state
          const notification: NotificationMessage = data;
          setNotifications((prev) => [notification, ...prev]);
          
          // Show toast notification based on severity
          switch (notification.severity) {
            case 'success':
              toast.success(notification.message);
              break;
            case 'error':
              toast.error(notification.message);
              break;
            case 'warning':
              toast(notification.message, { icon: '⚠️' });
              break;
            default:
              toast(notification.message);
          }
          
          onMessage?.(notification);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
        setIsConnected(false);
        wsRef.current = null;
        
        onDisconnect?.();

        // Auto-reconnect if enabled and not intentionally disconnected
        if (
          autoReconnect &&
          !isIntentionalDisconnectRef.current &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting in ${reconnectInterval}ms... (Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      // Set up ping interval to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000); // Ping every 30 seconds

      // Store interval ID for cleanup
      (ws as any).pingInterval = pingInterval;

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [user, token, getWebSocketUrl, onConnect, onDisconnect, autoReconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    isIntentionalDisconnectRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      // Clear ping interval
      const pingInterval = (wsRef.current as any).pingInterval;
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const markAsRead = useCallback((notificationId: string) => {
    const success = sendMessage({
      type: 'mark_read',
      notification_id: notificationId,
    });
    
    if (success) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
    }
    
    return success;
  }, [sendMessage]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Auto-connect when user logs in
  useEffect(() => {
    if (user && token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [user, token]); // Only reconnect when user or token changes

  return {
    isConnected,
    notifications,
    unreadCount: notifications.filter((n) => !n.read).length,
    sendMessage,
    markAsRead,
    clearNotifications,
    connect,
    disconnect,
  };
};