#!/bin/bash

# Frontend development server startup script

echo "Starting Cybersecurity Awareness Platform Frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Set environment variables
export VITE_API_URL="http://localhost:8000"
export VITE_APP_NAME="Cybersecurity Awareness Platform"

# Start the development server
echo "Starting Vite development server..."
npm run dev -- --host --port 3000