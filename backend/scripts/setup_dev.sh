#!/bin/bash

# Development setup script

echo "Setting up Cybersecurity Platform Backend..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your configuration"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p logs uploads alembic/versions

# Initialize database
echo "To initialize the database, run:"
echo "  alembic upgrade head"

echo ""
echo "Setup complete! To start development:"
echo "  1. Edit .env file with your configuration"
echo "  2. Start PostgreSQL database"
echo "  3. Run: alembic upgrade head"
echo "  4. Run: python main.py"