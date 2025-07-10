#!/bin/bash
# Script to run a single test with proper environment setup

set -e

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if not already installed
pip install -q pytest pytest-asyncio pytest-cov httpx aiosqlite

# Set test environment
export TESTING=true
export ENVIRONMENT=test
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export SECRET_KEY="test-secret-key"
export FRONTEND_URL="http://localhost:5173"

# Run the test
echo "Running test..."
python -m pytest tests/api/test_auth.py::TestAuthEndpoints::test_login_success -v --tb=short --no-header -x