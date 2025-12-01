#!/bin/bash

# AOC Dashboard Startup Script

echo "Starting AOC Device Control Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for Firebase credentials
if [ ! -f "firebase-service-account.json" ]; then
    echo "WARNING: Firebase service account file not found!"
    echo "Please download it from Firebase Console and save as 'firebase-service-account.json'"
    echo "Press Enter to continue anyway, or Ctrl+C to exit..."
    read
fi

# Create upload directories
mkdir -p uploads/apk

# Set default environment variables if not set
export FLASK_APP=${FLASK_APP:-app.py}
export FLASK_ENV=${FLASK_ENV:-development}
export FLASK_HOST=${FLASK_HOST:-0.0.0.0}
export FLASK_PORT=${FLASK_PORT:-5001}

# Start the application
echo "Starting Flask server on http://${FLASK_HOST}:${FLASK_PORT}"
python app.py

