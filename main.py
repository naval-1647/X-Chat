"""
Xchat API - Main entry point for deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import the app
from app import app

# Export app for uvicorn
__all__ = ["app"]