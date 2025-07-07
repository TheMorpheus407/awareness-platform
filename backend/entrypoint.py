#!/usr/bin/env python3
"""
Entrypoint for running the application with proper Python path setup.
"""
import os
import sys
import subprocess

# Ensure the app directory is in the Python path
app_dir = "/app"
if os.path.exists(app_dir):
    sys.path.insert(0, app_dir)

# Set environment variable
os.environ["PYTHONPATH"] = f"{app_dir}:{os.environ.get('PYTHONPATH', '')}"

# Get configuration from environment
workers = os.environ.get("WORKERS", "4")
port = os.environ.get("PORT", "8000")
log_level = os.environ.get("LOG_LEVEL", "info")

# Run gunicorn
cmd = [
    "gunicorn",
    "main:app",
    "-w", workers,
    "-k", "uvicorn.workers.UvicornWorker",
    "--bind", f"0.0.0.0:{port}",
    "--access-logfile", "-",
    "--error-logfile", "-",
    "--log-level", log_level
]

print(f"Starting application with PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"Command: {' '.join(cmd)}")

# Execute gunicorn
subprocess.run(cmd)