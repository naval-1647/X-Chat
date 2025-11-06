#!/bin/bash

# Start script for Render deployment
echo "Starting Xchat API server..."

# Use uvicorn for production with proper settings
exec uvicorn app:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --access-log \
    --no-server-header