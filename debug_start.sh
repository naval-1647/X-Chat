#!/bin/bash

# Deployment script for Render - ensures uvicorn is available
echo "=== Xchat Deployment Start Script ==="

# Show Python and pip versions
echo "Python version:"
python --version
echo "Pip version:"
pip --version

# Show installed packages
echo "Checking installed packages:"
pip list | grep -E "(fastapi|uvicorn)"

# Find uvicorn location
echo "Looking for uvicorn..."
which uvicorn || echo "uvicorn not found in PATH"
find /opt -name "uvicorn" 2>/dev/null || echo "uvicorn not found in /opt"

# Try different ways to run uvicorn
echo "Attempting to start server..."

# Method 1: Direct uvicorn command
if command -v uvicorn &> /dev/null; then
    echo "Using uvicorn command"
    exec uvicorn simple_app:app --host 0.0.0.0 --port $PORT
fi

# Method 2: Python module
echo "Using python -m uvicorn"
exec python -m uvicorn simple_app:app --host 0.0.0.0 --port $PORT