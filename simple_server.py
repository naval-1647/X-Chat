"""
Simple FastAPI server to test the /users/online endpoint
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="ChatX Simple Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Mock users data
mock_users = [
    {"id": "1", "username": "user1", "first_name": "John", "last_name": "Doe", "status": "online"},
    {"id": "2", "username": "user2", "first_name": "Jane", "last_name": "Smith", "status": "online"},
    {"id": "3", "username": "user3", "first_name": "Bob", "last_name": "Johnson", "status": "offline"},
]

def get_current_user(token = Depends(security)):
    """Mock authentication - accept any token"""
    return {"id": "current_user", "username": "current"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app_name": "ChatX Simple Test", "version": "1.0.0"}

@app.get("/api/v1/users/online")
async def get_online_users(current_user: dict = Depends(get_current_user)):
    """Get list of online users"""
    online_users = [user for user in mock_users if user["status"] == "online"]
    return online_users

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "avatar_url": None,
        "status": "online"
    }

@app.get("/api/v1/users/friends/list")
async def get_friends_list(current_user: dict = Depends(get_current_user)):
    """Get friends list"""
    return []

@app.get("/api/v1/users/friends/requests/received")
async def get_received_requests(current_user: dict = Depends(get_current_user)):
    """Get received friend requests"""
    return []

@app.get("/api/v1/users/friends/requests/sent")
async def get_sent_requests(current_user: dict = Depends(get_current_user)):
    """Get sent friend requests"""
    return []

@app.get("/api/v1/users/blocked/list")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    """Get blocked users list"""
    return []

@app.get("/api/v1/chats/")
async def get_chats(page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get chats list"""
    return {"chats": [], "total": 0, "page": page, "limit": limit}

@app.get("/api/v1/users/search")
async def search_users(q: str, page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Search for users"""
    # Mock search results
    all_users = [
        {"id": "1", "username": "naval12", "first_name": "Naval", "last_name": "Jha", "email": "naval@gmail.com", "avatar_url": None},
        {"id": "2", "username": "testuser", "first_name": "Test", "last_name": "User", "email": "test@example.com", "avatar_url": None},
        {"id": "3", "username": "john_doe", "first_name": "John", "last_name": "Doe", "email": "john@example.com", "avatar_url": None},
    ]
    
    # Filter users based on search query
    search_query = q.lower()
    filtered_users = [
        user for user in all_users 
        if (search_query in user["username"].lower() or 
            search_query in user["first_name"].lower() or 
            search_query in user["last_name"].lower() or 
            search_query in user["email"].lower())
    ]
    
    return {
        "users": filtered_users,
        "total": len(filtered_users),
        "page": page,
        "limit": limit
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)