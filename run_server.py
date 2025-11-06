#!/usr/bin/env python3
"""
Direct server runner - bypasses uvicorn command issues
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_server():
    """Run the server directly using uvicorn programmatically"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
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
        print("Available packages:")
        try:
            import subprocess
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