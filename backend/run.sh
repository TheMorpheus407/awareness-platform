#!/bin/bash
set -e

# Set Python path to current directory
export PYTHONPATH=/mnt/e/Projects/AwarenessSchulungen/backend:$PYTHONPATH

# Default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "Starting backend with PYTHONPATH: $PYTHONPATH"

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