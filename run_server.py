"""
Direct server runner - bypasses uvicorn command issues
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_server():
    """Run the server directly using uvicorn programmatically"""
    try:
        import uvicorn
        from simple_app import app
        
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting server on port {port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Available packages:")
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
        print(result.stdout)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()