#!/usr/bin/env python3
"""Create initial admin user for the platform"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.append('/app')

from core.database import async_session
from models.user import User
from core.security import get_password_hash


async def create_admin_user():
    """Create the initial admin user"""
    async with async_session() as session:
        # Check if admin already exists
        existing = await session.execute(
            select(User).where(User.email == "admin@bootstrap-awareness.de")
        )
        if existing.scalar_one_or_none():
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email="admin@bootstrap-awareness.de",
            password_hash=get_password_hash("ChangeMe123!"),
            first_name="Platform",
            last_name="Administrator",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            verified_at=datetime.utcnow()
        )
        
        session.add(admin)
        await session.commit()
        
        print("=" * 60)
        print("Admin user created successfully!")
        print("=" * 60)
        print("Email: admin@bootstrap-awareness.de")
        print("Password: ChangeMe123!")
        print("IMPORTANT: Please change this password immediately!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_admin_user())