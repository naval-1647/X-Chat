#!/bin/bash

# Build script that ensures packages are installed correctly
echo "=== Build Script Starting ==="

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements with verbose output
echo "Installing requirements..."
pip install -r requirements.txt --verbose

# Verify installation
echo "Verifying installation..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
python -c "import uvicorn; print(f'Uvicorn version: {uvicorn.__version__}')"

# Check if uvicorn command is available
echo "Checking uvicorn command..."
which uvicorn || echo "uvicorn command not found, will use python -m uvicorn"

echo "=== Build Script Complete ==="