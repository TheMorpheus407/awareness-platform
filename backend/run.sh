#!/bin/bash
set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Set Python path to current directory
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

# Default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "Starting backend with PYTHONPATH: $PYTHONPATH"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Dependencies not installed. Installing..."
    pip install -r requirements.txt
fi

# Run with uvicorn in development mode
if [ "$ENVIRONMENT" = "development" ] || [ "$DEBUG" = "true" ]; then
    echo "Running in development mode with auto-reload"
    exec uvicorn main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level $LOG_LEVEL
else
    echo "Running in production mode"
    exec python entrypoint.py
fi