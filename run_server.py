#!/usr/bin/env python3
"""
Direct server runner - bypasses uvicorn command issues
"""
import os
import sys
import subprocess
import site

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def find_venv_packages():
    """Find and add virtual environment packages to Python path"""
    # Look for common virtual environment locations
    possible_venv_paths = [
        "/opt/render/project/src/.venv/lib/python3.11/site-packages",
        "/opt/render/project/src/.venv/lib/python3.13/site-packages", 
        "/opt/render/project/.venv/lib/python3.11/site-packages",
        "/opt/render/project/.venv/lib/python3.13/site-packages",
        "/home/render/.local/lib/python3.11/site-packages",
        "/usr/local/lib/python3.11/site-packages",
    ]
    
    print("Searching for virtual environment packages...")
    for path in possible_venv_paths:
        if os.path.exists(path):
            print(f"Found packages directory: {path}")
            if path not in sys.path:
                sys.path.insert(0, path)
                print(f"Added to Python path: {path}")
    
    # Also try to find packages using pip show
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", "uvicorn"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Location:'):
                    location = line.split(':', 1)[1].strip()
                    print(f"Found uvicorn location: {location}")
                    if location not in sys.path:
                        sys.path.insert(0, location)
                        print(f"Added uvicorn location to path: {location}")
    except Exception as e:
        print(f"Could not find uvicorn location: {e}")

def run_server():
    """Run the server directly using uvicorn programmatically"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Try to find and add virtual environment packages
    find_venv_packages()
    
    print(f"Updated Python path: {sys.path[:3]}...") # Show first 3 entries
    
    try:
        print("Importing uvicorn...")
        import uvicorn
        print(f"Uvicorn version: {uvicorn.__version__}")
        
        print("Importing app...")
        from simple_app import app
        print("App imported successfully")
        
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting server on 0.0.0.0:{port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Final attempt - checking all possible package locations...")
        
        # List all possible Python package directories
        print("Checking filesystem for packages...")
        try:
            result = subprocess.run(["find", "/opt", "-name", "uvicorn*", "-type", "d"], 
                                  capture_output=True, text=True, timeout=10)
            if result.stdout:
                print("Found uvicorn directories:")
                print(result.stdout)
        except Exception:
            pass
            
        print("Available packages from pip:")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
            print(result.stdout)
        except Exception as pip_error:
            print(f"Could not list packages: {pip_error}")
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_server()