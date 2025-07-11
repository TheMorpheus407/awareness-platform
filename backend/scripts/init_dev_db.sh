#!/bin/bash
# Development database initialization script

set -e

echo "=== Development Database Initialization ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run the initialization script
echo "Running database initialization..."
python scripts/init_database.py

# Optional: Create test data
if [ "$1" == "--with-test-data" ]; then
    echo "Creating test data..."
    python scripts/create_test_data.py
fi

echo "=== Development database ready! ===">