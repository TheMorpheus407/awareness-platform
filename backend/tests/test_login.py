#!/usr/bin/env python3
"""Test login endpoint directly"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override DATABASE_URL before importing anything
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_db.db'

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import bcrypt

async def test_login():
    # Create database engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test_db.db",
        echo=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        # Create users table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user',
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Hash password
        password = "admin123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert admin user
        await conn.execute(text("""
            INSERT OR REPLACE INTO users (email, hashed_password, is_active, is_verified, role, first_name, last_name)
            VALUES (:email, :password, 1, 1, 'admin', 'Admin', 'User')
        """), {"email": "admin@bootstrap-academy.com", "password": hashed})
        
        await conn.commit()
    
    # Test password verification
    async with AsyncSession(engine) as session:
        result = await session.execute(
            text("SELECT email, hashed_password FROM users WHERE email = :email"),
            {"email": "admin@bootstrap-academy.com"}
        )
        user = result.fetchone()
        if user:
            print(f"Found user: {user.email}")
            print(f"Stored hash: {user.hashed_password}")
            print(f"Password check: {bcrypt.checkpw(b'admin123', user.hashed_password.encode('utf-8'))}")
        else:
            print("User not found!")
    
    await engine.dispose()
    print("\nDatabase setup complete. Admin user created.")
    print("Email: admin@bootstrap-academy.com")
    print("Password: admin123")

if __name__ == "__main__":
    asyncio.run(test_login())