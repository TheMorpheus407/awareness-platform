#!/usr/bin/env python3
"""Minimal test server for login functionality"""
import os
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_db.db'

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from pydantic import BaseModel
import bcrypt
from datetime import datetime, timedelta
import jwt

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_async_engine("sqlite+aiosqlite:///./test_db.db", echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

# Secret key for JWT
SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Query user
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": request.email}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password
    if not bcrypt.checkpw(request.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_access_token({"sub": user.email, "user_id": user.id, "refresh": True})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    )

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"message": "Test server running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)