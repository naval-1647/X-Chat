"""
Simple FastAPI server for deployment - bypasses complex import issues
"""
import os
import sys
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Simple FastAPI app without complex imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create simple app
app = FastAPI(
    title="Xchat API", 
    description="Simple deployment version",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Xchat API is running!", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "app": "Xchat API"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "version": "1.0.0"}

# Basic test endpoint
@app.post("/api/v1/test")
async def test_endpoint(data: dict = None):
    return {"message": "Test endpoint working", "received": data or {}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)