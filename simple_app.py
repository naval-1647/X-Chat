"""
Simple FastAPI server for deployment - bypasses complex import issues
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {"message": "Xchat API is running!", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "app": "Xchat API", "message": "Service is operational"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "version": "1.0.0", "api": "v1"}

# Basic test endpoint
@app.post("/api/v1/test")
async def test_endpoint(data: dict = None):
    return {"message": "Test endpoint working", "received": data or {}, "status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)