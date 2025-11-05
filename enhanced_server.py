"""
Enhanced FastAPI server with proper endpoint integration
Based on the original ChatX backend but simplified for development
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="ChatX API",
    description="Real-Time Messaging Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Mock data
mock_users = [
    {
        "id": "1",
        "username": "naval12",
        "email": "naval@gmail.com",
        "first_name": "Naval",
        "last_name": "Jha",
        "avatar_url": None,
        "status": "online",
        "last_seen": datetime.now().isoformat(),
        "is_active": True
    },
    {
        "id": "2",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "avatar_url": None,
        "status": "online",
        "last_seen": datetime.now().isoformat(),
        "is_active": True
    },
    {
        "id": "3",
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "avatar_url": None,
        "status": "offline",
        "last_seen": datetime.now().isoformat(),
        "is_active": True
    },
]

mock_current_user = {
    "id": "current_user_123",
    "username": "currentuser",
    "email": "current@example.com",
    "first_name": "Current",
    "last_name": "User",
    "avatar_url": None,
    "status": "online",
    "last_seen": datetime.now().isoformat(),
    "is_active": True
}

def get_current_user(token = Depends(security)):
    """Mock authentication - accept any token"""
    return mock_current_user

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": "ChatX API",
        "version": "1.0.0",
        "debug": True
    }

# Auth endpoints
@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/v1/auth/login")
async def login(request: Optional[LoginRequest] = None):
    """Mock login endpoint"""
    # Mock login - accept any credentials
    return {
        "access_token": "mock_token_123", 
        "token_type": "bearer",
        "user": mock_current_user
    }

@app.post("/api/v1/auth/register")
async def register():
    """Mock register endpoint"""
    return {
        "message": "User registered successfully",
        "user": mock_current_user
    }

# User endpoints
@app.get("/api/v1/users/online")
async def get_online_users(current_user: dict = Depends(get_current_user)):
    """Get list of online users"""
    online_users = [user for user in mock_users if user["status"] == "online"]
    return online_users

@app.get("/api/v1/users/search")
async def search_users(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """Search for users"""
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must be at least 2 characters long"
        )
    
    search_query = q.lower().strip()
    filtered_users = []
    
    for user in mock_users:
        if (search_query in user["username"].lower() or 
            search_query in user["first_name"].lower() or 
            search_query in user["last_name"].lower() or 
            search_query in user["email"].lower()):
            # Don't include current user in search results
            if user["id"] != current_user["id"]:
                filtered_users.append({
                    "id": user["id"],
                    "username": user["username"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "email": user["email"],
                    "avatar_url": user["avatar_url"]
                })
    
    return {
        "users": filtered_users,
        "total": len(filtered_users),
        "page": page,
        "limit": limit
    }

# Friends endpoints
@app.get("/api/v1/users/friends/list")
async def get_friends_list(current_user: dict = Depends(get_current_user)):
    """Get friends list"""
    return []

@app.post("/api/v1/users/friends/request")
async def send_friend_request(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Send friend request"""
    return {"message": "Friend request sent successfully"}

@app.get("/api/v1/users/friends/requests/received")
async def get_received_requests(current_user: dict = Depends(get_current_user)):
    """Get received friend requests"""
    return []

@app.get("/api/v1/users/friends/requests/sent")
async def get_sent_requests(current_user: dict = Depends(get_current_user)):
    """Get sent friend requests"""
    return []

@app.post("/api/v1/users/friends/requests/{request_id}/accept")
async def accept_friend_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept friend request"""
    return {"message": "Friend request accepted"}

@app.post("/api/v1/users/friends/requests/{request_id}/reject")
async def reject_friend_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Reject friend request"""
    return {"message": "Friend request rejected"}

# Blocking endpoints
@app.get("/api/v1/users/blocked/list")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    """Get blocked users list"""
    return []

@app.post("/api/v1/users/{user_id}/block")
async def block_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Block a user"""
    return {"message": "User blocked successfully"}

@app.delete("/api/v1/users/{user_id}/block")
async def unblock_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unblock a user"""
    return {"message": "User unblocked successfully"}

# Chat endpoints
@app.get("/api/v1/chats/")
async def get_chats(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get chats list"""
    return {
        "chats": [],
        "total": 0,
        "page": page,
        "limit": limit
    }

@app.post("/api/v1/chats/")
async def create_chat(current_user: dict = Depends(get_current_user)):
    """Create a new chat"""
    return {
        "id": "new_chat_123",
        "name": "New Chat",
        "type": "direct",
        "created_at": datetime.now().isoformat()
    }

@app.get("/api/v1/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get chat messages"""
    return {
        "messages": [],
        "total": 0,
        "page": page,
        "limit": limit
    }

@app.post("/api/v1/chats/{chat_id}/messages")
async def send_message(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Send a message"""
    return {
        "id": "new_message_123",
        "content": "Message sent",
        "sender_id": current_user["id"],
        "chat_id": chat_id,
        "created_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)