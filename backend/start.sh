#!/bin/bash
# Startup script for the backend application

# Ensure we're in the correct directory
cd /app

# Add the current directory to PYTHONPATH
export PYTHONPATH=/app:$PYTHONPATH

# Log the Python path for debugging
echo "Starting application with PYTHONPATH: $PYTHONPATH"
echo "Current directory: $(pwd)"

# Run the application with gunicorn
exec gunicorn main:app \
    -w ${WORKERS:-4} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info}