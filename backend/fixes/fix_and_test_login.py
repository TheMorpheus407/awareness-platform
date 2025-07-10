#!/usr/bin/env python3
"""Fix backend configuration and test login"""
import os
import sys
import requests
import time
import subprocess
import signal
from datetime import datetime

# First, create a minimal config that works
minimal_env = """
APP_NAME="Cybersecurity Awareness Platform"
APP_VERSION="1.0.0"
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
WORKERS=1
LOG_LEVEL=INFO

SECRET_KEY=dev-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=sqlite+aiosqlite:///./test_auth.db
REDIS_URL=redis://localhost:6379/0

FRONTEND_URL=http://localhost:3000

SMTP_HOST=localhost
SMTP_PORT=587
EMAIL_FROM_EMAIL=noreply@example.com
EMAIL_FROM_NAME="Test Platform"
""".strip()

def create_test_db():
    """Create test database with admin user"""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    import bcrypt
    
    async def setup():
        engine = create_async_engine("sqlite+aiosqlite:///./test_auth.db")
        
        async with engine.begin() as conn:
            # Create users table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 1,
                    is_superuser BOOLEAN DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    first_name TEXT,
                    last_name TEXT,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    two_factor_secret TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create companies table (may be needed)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create admin user with the expected credentials
            password = "admin123"
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO users 
                (email, password_hash, is_active, is_verified, is_superuser, role, first_name, last_name)
                VALUES (:email, :password, 1, 1, 1, 'admin', 'Admin', 'User')
            """), {"email": "admin@bootstrap-academy.com", "password": hashed})
            
            print("✅ Database created with admin user")
    
    asyncio.run(setup())

def test_login():
    """Test the login endpoint"""
    print("\n🔐 Testing login endpoint...")
    
    # Test with form data (OAuth2 format)
    response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={
            "username": "admin@bootstrap-academy.com",
            "password": "admin123"
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"Access Token: {data.get('access_token', '')[:50]}...")
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
    except:
        pass
    return False

if __name__ == "__main__":
    print("🚀 Fixing backend and testing login...")
    
    # Create minimal env
    with open(".env.test", "w") as f:
        f.write(minimal_env)
    
    # Create test database
    create_test_db()
    
    # Start backend
    print("\n🔧 Starting backend server...")
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./test_auth.db"
    
    # Start server in background
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    for i in range(10):
        time.sleep(1)
        if test_health():
            break
    else:
        print("❌ Server failed to start")
        server.terminate()
        sys.exit(1)
    
    # Test login
    success = test_login()
    
    # Cleanup
    server.terminate()
    
    if success:
        print("\n✅ LOGIN IS WORKING!")
        print("Credentials:")
        print("  Email: admin@bootstrap-academy.com")
        print("  Password: admin123")
    else:
        print("\n❌ LOGIN FAILED!")
        sys.exit(1)