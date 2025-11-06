#!/bin/bash

# Robust start script that finds the correct Python with packages
echo "=== Finding Python with installed packages ==="

# Function to test if Python has uvicorn
test_python() {
    local python_cmd="$1"
    echo "Testing: $python_cmd"
    if command -v "$python_cmd" &> /dev/null; then
        if "$python_cmd" -c "import uvicorn; print('✅ uvicorn found')" 2>/dev/null; then
            echo "✅ $python_cmd has uvicorn"
            return 0
        else
            echo "❌ $python_cmd missing uvicorn"
            return 1
        fi
    else
        echo "❌ $python_cmd not found"
        return 1
    fi
}

# List of Python interpreters to try
PYTHON_COMMANDS=(
    "python3"
    "python"
    "/opt/render/project/src/.venv/bin/python"
    "/opt/render/project/src/.venv/bin/python3"
    "/usr/local/bin/python3"
    "~/.local/bin/python3"
)

# Find working Python
WORKING_PYTHON=""
for cmd in "${PYTHON_COMMANDS[@]}"; do
    if test_python "$cmd"; then
        WORKING_PYTHON="$cmd"
        break
    fi
done

if [ -z "$WORKING_PYTHON" ]; then
    echo "❌ No Python interpreter found with uvicorn installed"
    echo "Available Python interpreters:"
    find /usr -name "python*" -type f 2>/dev/null | head -5
    find /opt -name "python*" -type f 2>/dev/null | head -5
    exit 1
fi

echo "🚀 Starting server with: $WORKING_PYTHON"
exec "$WORKING_PYTHON" -m uvicorn simple_app:app --host 0.0.0.0 --port "$PORT"