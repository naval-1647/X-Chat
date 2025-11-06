"""
Xchat API - Main entry point for deployment
"""
import os
import sys

# Add the current directory to Python path to ensure app module can find its submodules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Also add the app directory itself to ensure all internal imports work
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Set PYTHONPATH environment variable as well
os.environ['PYTHONPATH'] = current_dir + ':' + os.environ.get('PYTHONPATH', '')

try:
    # Now import the app
    from app import app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    print(f"Files in current dir: {os.listdir(current_dir)}")
    if os.path.exists(app_dir):
        print(f"Files in app dir: {os.listdir(app_dir)}")
    raise

# Export app for uvicorn
__all__ = ["app"]