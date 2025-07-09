#!/usr/bin/env python3
"""Script to create a superuser for initial setup."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from core.security import get_password_hash
from db.session import AsyncSessionLocal
from models.user import User


async def create_superuser():
    """Create a superuser account."""
    print("Creating superuser...")
    
    # Get user input
    email = input("Email: ").strip()
    if not email:
        print("Email is required!")
        return
    
    password = input("Password: ").strip()
    if not password or len(password) < 8:
        print("Password must be at least 8 characters!")
        return
    
    first_name = input("First name: ").strip() or "Admin"
    last_name = input("Last name: ").strip() or "User"
    
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"User with email {email} already exists!")
            return
        
        # Create superuser
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role="admin",
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )
        
        session.add(user)
        await session.commit()
        
        print(f"Superuser {email} created successfully!")


if __name__ == "__main__":
    asyncio.run(create_superuser())