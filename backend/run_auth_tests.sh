#!/bin/bash

# Script to run authentication tests

echo "Running Authentication Tests..."
echo "=============================="

# Change to backend directory
cd /mnt/e/Projects/AwarenessSchulungen/backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run specific auth tests
echo "Running auth tests with pytest..."
python -m pytest tests/test_auth.py -v --tb=short

# Run with coverage if needed
# python -m pytest tests/test_auth.py -v --cov=api.routes.auth --cov=core.security --cov-report=term-missing

echo ""
echo "Test run complete!"