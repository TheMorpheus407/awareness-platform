"""
Test script for WebSocket notifications.

Run this after starting the backend server:
    python test_websocket.py
"""

import asyncio
import websockets
import json
import httpx
from datetime import datetime


class WebSocketTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        
    async def login(self):
        """Login to get JWT token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": "admin@test.com",  # Update with your test user
                    "password": "admin123"  # Update with your test password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"✅ Logged in successfully")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(response.text)
                return False
    
    async def connect_websocket(self):
        """Connect to WebSocket and listen for notifications."""
        if not self.token:
            print("❌ No token available. Please login first.")
            return
            
        ws_url = f"ws://localhost:8000/api/v1/notifications/ws?token={self.token}"
        print(f"🔌 Connecting to WebSocket...")
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket connected!")
                
                # Send initial ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Listen for messages
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data.get("type") == "pong":
                        print("🏓 Received pong")
                    else:
                        print(f"\n📨 New notification received:")
                        print(f"   Type: {data.get('type')}")
                        print(f"   Title: {data.get('title')}")
                        print(f"   Message: {data.get('message')}")
                        print(f"   Severity: {data.get('severity')}")
                        print(f"   Time: {data.get('timestamp')}")
                        if data.get('data'):
                            print(f"   Data: {json.dumps(data.get('data'), indent=2)}")
                        
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"❌ WebSocket connection closed: {e}")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def send_test_notification(self):
        """Send a test notification via API."""
        if not self.token:
            print("❌ No token available. Please login first.")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/notifications/test",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "notification_type": "test",
                    "title": "Test Notification",
                    "message": f"This is a test notification sent at {datetime.now().strftime('%H:%M:%S')}",
                    "severity": "info"
                }
            )
            
            if response.status_code == 200:
                print("✅ Test notification sent successfully")
            else:
                print(f"❌ Failed to send notification: {response.status_code}")
                print(response.text)
    
    async def run_interactive_test(self):
        """Run interactive test session."""
        print("🚀 WebSocket Notification Test")
        print("=" * 50)
        
        # Login
        if not await self.login():
            return
            
        # Create tasks for WebSocket connection and user input
        websocket_task = asyncio.create_task(self.connect_websocket())
        
        # Wait a bit for connection to establish
        await asyncio.sleep(2)
        
        # Interactive loop
        print("\nCommands:")
        print("  1 - Send test notification")
        print("  2 - Send success notification")
        print("  3 - Send warning notification")
        print("  4 - Send error notification")
        print("  q - Quit")
        print("\nWaiting for notifications...")
        
        while True:
            # Non-blocking input would be better, but for simplicity:
            await asyncio.sleep(1)
            
            # Send a test notification every 10 seconds
            if int(datetime.now().timestamp()) % 10 == 0:
                await self.send_test_notification()
                await asyncio.sleep(1)  # Prevent multiple sends


async def main():
    """Main function."""
    tester = WebSocketTester()
    
    # Run the interactive test
    try:
        await tester.run_interactive_test()
    except KeyboardInterrupt:
        print("\n\n👋 Test terminated by user")


if __name__ == "__main__":
    asyncio.run(main())