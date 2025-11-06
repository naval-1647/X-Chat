#!/bin/bash

# Robust start script that handles different Python command variations
echo "=== Starting Xchat API Server ==="

# Show environment
echo "Environment variables:"
env | grep -E "(PYTHON|PATH)" || echo "No Python env vars found"

echo "Checking available Python commands..."

# Try to find Python
if command -v python3 &> /dev/null; then
    echo "Using python3"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "Using python"
    PYTHON_CMD="python"
elif command -v python3.11 &> /dev/null; then
    echo "Using python3.11"
    PYTHON_CMD="python3.11"
elif command -v python3.13 &> /dev/null; then
    echo "Using python3.13"
    PYTHON_CMD="python3.13"
else
    echo "ERROR: No Python interpreter found!"
    echo "Available commands:"
    ls -la /usr/bin/python* || echo "No python in /usr/bin"
    ls -la /opt/render/project/python/*/bin/python* || echo "No python in render project"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"
$PYTHON_CMD --version

# Start the server
echo "Starting server with $PYTHON_CMD..."
exec $PYTHON_CMD run_server.py