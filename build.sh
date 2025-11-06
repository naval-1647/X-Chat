#!/bin/bash

# Build script for Render deployment
set -o errexit  # Exit on error

echo "Installing Python dependencies..."
pip install --upgrade pip
#!/bin/bash

# Ensure we're using Python 3.11
python --version
pip --version

# Upgrade pip to latest version
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads/messages
mkdir -p uploads/avatars

echo "Creating uploads directory..."
mkdir -p uploads

echo "Build completed successfully!"