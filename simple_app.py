"""
Enhanced ChatX API with basic functionality
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import jwt
import time
from datetime import datetime, timedelta

# Create app
app = FastAPI(
    title="Xchat API", 
    description="Real-time messaging API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (for demo - use database in production)
users_db = {}
messages_db = []
chats_db = {}

# JWT Secret
JWT_SECRET = "your-secret-key-change-in-production"

# Pydantic Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    chat_id: str
    content: str
    sender_id: str

class ChatCreate(BaseModel):
    name: str
    participants: List[str]

# Helper Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Root Endpoints
@app.get("/")
async def root():
    return {
        "message": "Xchat API is running!", 
        "status": "healthy", 
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "users": "/api/v1/users/",
            "chats": "/api/v1/chats/",
            "messages": "/api/v1/messages/",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "app": "Xchat API", 
        "message": "Service is operational",
        "users_count": len(users_db),
        "messages_count": len(messages_db),
        "chats_count": len(chats_db)
    }

# Authentication Endpoints
@app.post("/api/v1/auth/register")
async def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = f"user_{len(users_db) + 1}"
    users_db[user.username] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": datetime.utcnow().isoformat()
    }
    
    token = create_token(user_id)
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "username": user.username,
        "token": token
    }

@app.post("/api/v1/auth/login")
async def login(credentials: UserLogin):
    user = users_db.get(credentials.username)
    if not user or user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return {
        "message": "Login successful",
        "user_id": user["id"],
        "username": user["username"],
        "token": token
    }

# User Endpoints
@app.get("/api/v1/users")
async def get_users():
    users_list = []
    for username, user in users_db.items():
        users_list.append({
            "id": user["id"],
            "username": user["username"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        })
    return {"users": users_list}

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    for user in users_db.values():
        if user["id"] == user_id:
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
    raise HTTPException(status_code=404, detail="User not found")

# Chat Endpoints
@app.post("/api/v1/chats")
async def create_chat(chat: ChatCreate):
    chat_id = f"chat_{len(chats_db) + 1}"
    chats_db[chat_id] = {
        "id": chat_id,
        "name": chat.name,
        "participants": chat.participants,
        "created_at": datetime.utcnow().isoformat(),
        "message_count": 0
    }
    return {"message": "Chat created", "chat_id": chat_id, "chat": chats_db[chat_id]}

@app.get("/api/v1/chats")
async def get_chats():
    return {"chats": list(chats_db.values())}

@app.get("/api/v1/chats/{chat_id}")
async def get_chat(chat_id: str):
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"chat": chats_db[chat_id]}

# Message Endpoints
@app.post("/api/v1/messages")
async def send_message(message: Message):
    if message.chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    msg_id = f"msg_{len(messages_db) + 1}"
    new_message = {
        "id": msg_id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "content": message.content,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text"
    }
    
    messages_db.append(new_message)
    chats_db[message.chat_id]["message_count"] += 1
    
    return {"message": "Message sent", "message_id": msg_id, "data": new_message}

@app.get("/api/v1/messages/{chat_id}")
async def get_messages(chat_id: str):
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_messages = [msg for msg in messages_db if msg["chat_id"] == chat_id]
    return {"messages": chat_messages}

# Test Endpoints
@app.get("/api/v1/test")
async def test_get():
    return {
        "message": "GET test endpoint working",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

@app.post("/api/v1/test")
async def test_post(data: dict = None):
    return {
        "message": "POST test endpoint working", 
        "received": data or {}, 
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)