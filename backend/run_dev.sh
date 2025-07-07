#!/bin/bash

# Development server startup script

echo "Starting Cybersecurity Awareness Platform Backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://awareness:awareness123@localhost:5432/awareness_platform"
export REDIS_URL="redis://default:redis123@localhost:6379"
export SECRET_KEY="devsecretkey123456789012345678901234567890"
export JWT_SECRET_KEY="devjwtsecret123456789012345678901234567890"
export ENVIRONMENT="development"
export DEBUG="true"
export CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Seed database (if needed)
if [ "$1" == "--seed" ]; then
    echo "Seeding database..."
    python scripts/seed_data.py
fi

# Start the server
echo "Starting FastAPI server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000