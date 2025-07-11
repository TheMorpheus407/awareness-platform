import React, { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

export const NotificationTest: React.FC = () => {
  const [notificationType, setNotificationType] = useState('test');
  const [title, setTitle] = useState('Test Notification');
  const [message, setMessage] = useState('This is a test notification');
  const [severity, setSeverity] = useState<'info' | 'warning' | 'error' | 'success'>('info');
  const [isLoading, setIsLoading] = useState(false);
  
  const api = useApi();

  const sendTestNotification = async () => {
    setIsLoading(true);
    try {
      await api.post('/notifications/test', {
        notification_type: notificationType,
        title,
        message,
        severity,
      });
      toast.success('Test notification sent!');
    } catch (error) {
      toast.error('Failed to send notification');
      console.error('Error sending notification:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const notificationTypes = [
    { value: 'test', label: 'Test' },
    { value: 'course_update', label: 'Course Update' },
    { value: 'quiz_result', label: 'Quiz Result' },
    { value: 'certificate_ready', label: 'Certificate Ready' },
    { value: 'phishing_result', label: 'Phishing Result' },
    { value: 'system_maintenance', label: 'System Maintenance' },
  ];

  const severityOptions = [
    { value: 'info', label: 'Info', color: 'text-blue-600' },
    { value: 'success', label: 'Success', color: 'text-green-600' },
    { value: 'warning', label: 'Warning', color: 'text-yellow-600' },
    { value: 'error', label: 'Error', color: 'text-red-600' },
  ];

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">WebSocket Notification Test</h1>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Send Test Notification</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notification Type
              </label>
              <Select
                value={notificationType}
                onChange={(e) => setNotificationType(e.target.value)}
                className="w-full"
              >
                {notificationTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <Input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Notification title"
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <Input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Notification message"
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity
              </label>
              <Select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as any)}
                className="w-full"
              >
                {severityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            <Button
              onClick={sendTestNotification}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Sending...' : 'Send Notification'}
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Preview</h2>
          
          <div className="space-y-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-start space-x-3">
                <div
                  className={`w-5 h-5 rounded-full ${
                    severity === 'success'
                      ? 'bg-green-500'
                      : severity === 'error'
                      ? 'bg-red-500'
                      : severity === 'warning'
                      ? 'bg-yellow-500'
                      : 'bg-blue-500'
                  }`}
                />
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{message}</p>
                  <div className="flex items-center mt-2 text-xs text-gray-500">
                    <span>Just now</span>
                    <span className="mx-2">•</span>
                    <span className="capitalize">{notificationType.replace(/_/g, ' ')}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Instructions:</h3>
              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                <li>Make sure you're logged in</li>
                <li>Open the notification center (bell icon in the navbar)</li>
                <li>Send a test notification using the form</li>
                <li>The notification should appear in real-time</li>
                <li>Try different notification types and severities</li>
              </ol>
            </div>
          </div>
        </Card>
      </div>

      <Card className="mt-6 p-6">
        <h2 className="text-xl font-semibold mb-4">WebSocket Connection Info</h2>
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-medium">Endpoint:</span>{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">
              ws://localhost:8000/api/v1/notifications/ws
            </code>
          </p>
          <p>
            <span className="font-medium">Authentication:</span> JWT token passed as query parameter
          </p>
          <p>
            <span className="font-medium">Auto-reconnect:</span> Enabled with exponential backoff
          </p>
          <p>
            <span className="font-medium">Heartbeat:</span> Ping/pong every 30 seconds
          </p>
        </div>
      </Card>
    </div>
  );
};