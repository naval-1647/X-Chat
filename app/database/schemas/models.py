"""
Request/Response models for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from app.database.schemas import UserStatus, MessageType, ChatType, FriendRequestStatus, NotificationType


# Authentication Models
class UserRegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None


class UserLoginRequest(BaseModel):
    """User login request"""
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# User Profile Models
class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    profile: Dict[str, Any]
    status: UserStatus
    last_seen: datetime
    is_verified: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)


class UserStatusUpdateRequest(BaseModel):
    """User status update request"""
    status: UserStatus


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


# Chat Models
class ChatCreateRequest(BaseModel):
    """Chat creation request"""
    type: Optional[ChatType] = None
    chat_type: Optional[str] = None  # Alternative field name for frontend compatibility
    participant_ids: Optional[List[str]] = None
    participants: Optional[List[str]] = None  # Alternative field name for frontend compatibility
    name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)  # Alternative field name
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('type', pre=True, always=True)
    def set_type(cls, v, values):
        if v is not None:
            return v
        if 'chat_type' in values and values['chat_type']:
            return values['chat_type']
        return ChatType.DIRECT  # Default to direct chat
    
    @validator('participant_ids', pre=True, always=True)  
    def set_participant_ids(cls, v, values):
        if v is not None:
            return v
        if 'participants' in values and values['participants']:
            return values['participants']
        return []
    
    @validator('name', pre=True, always=True)
    def set_name(cls, v, values):
        if v is not None:
            return v
        if 'title' in values and values['title']:
            return values['title']
        return None


class ChatUpdateRequest(BaseModel):
    """Chat update request"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ChatParticipantResponse(BaseModel):
    """Chat participant response"""
    user_id: str
    username: str
    full_name: str
    avatar_url: Optional[str]
    joined_at: datetime
    is_admin: bool
    is_muted: bool
    last_read_at: Optional[datetime]


class ChatResponse(BaseModel):
    """Chat response"""
    id: str
    type: ChatType
    name: Optional[str]
    description: Optional[str]
    avatar_url: Optional[str]
    participants: List[ChatParticipantResponse]
    created_by: str
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    is_archived: bool
    is_pinned: bool


class AddParticipantsRequest(BaseModel):
    """Add participants to chat request"""
    user_ids: List[str]


class UpdateParticipantRequest(BaseModel):
    """Update participant request"""
    is_admin: Optional[bool] = None
    is_muted: Optional[bool] = None


# Message Models
class MessageSendRequest(BaseModel):
    """Message send request"""
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[str] = None
    mentions: Optional[List[str]] = None


class MessageUpdateRequest(BaseModel):
    """Message update request"""
    content: str


class MessageReactionRequest(BaseModel):
    """Message reaction request"""
    emoji: str


class MessageMediaResponse(BaseModel):
    """Message media response"""
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    thumbnail_url: Optional[str]
    duration: Optional[int]
    dimensions: Optional[Dict[str, int]]


class MessageReactionResponse(BaseModel):
    """Message reaction response"""
    emoji: str
    user_id: str
    username: str
    created_at: datetime


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    content: Optional[str]
    message_type: MessageType
    media: Optional[MessageMediaResponse]
    chat_id: str
    sender_id: str
    sender_username: str
    sender_full_name: str
    reply_to_message_id: Optional[str]
    reactions: List[MessageReactionResponse]
    mentions: List[str]
    is_edited: bool
    edited_at: Optional[datetime]
    delivered_to: List[str]
    seen_by: List[Dict[str, Any]]
    created_at: datetime


class MessageHistoryRequest(BaseModel):
    """Message history request"""
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
    before_message_id: Optional[str] = None
    after_message_id: Optional[str] = None


class MessageSearchRequest(BaseModel):
    """Message search request"""
    query: str
    message_type: Optional[MessageType] = None
    sender_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)


# Friend Request Models
class FriendRequestSendRequest(BaseModel):
    """Send friend request"""
    user_id: str
    message: Optional[str] = Field(None, max_length=200)


class FriendRequestResponse(BaseModel):
    """Friend request response"""
    id: str
    sender_id: str
    sender_username: str
    sender_full_name: str
    receiver_id: str
    receiver_username: str
    receiver_full_name: str
    status: str  # Changed from FriendRequestStatus to str for proper JSON serialization
    message: Optional[str]
    created_at: datetime
    responded_at: Optional[datetime]


class FriendRequestActionRequest(BaseModel):
    """Friend request action (accept/reject)"""
    action: str = Field(..., pattern="^(accept|reject)$")


# Notification Models
class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    type: NotificationType
    title: str
    message: str
    related_user_id: Optional[str]
    related_chat_id: Optional[str]
    related_message_id: Optional[str]
    is_read: bool
    data: Optional[Dict[str, Any]]
    created_at: datetime
    read_at: Optional[datetime]


class NotificationUpdateRequest(BaseModel):
    """Mark notifications as read"""
    notification_ids: List[str]


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TypingIndicatorMessage(BaseModel):
    """Typing indicator WebSocket message"""
    type: str = "typing"
    chat_id: str
    user_id: str
    is_typing: bool


class PresenceUpdateMessage(BaseModel):
    """Presence update WebSocket message"""
    type: str = "presence"
    user_id: str
    status: UserStatus
    last_seen: datetime


class NewMessageNotification(BaseModel):
    """New message WebSocket notification"""
    type: str = "new_message"
    message: MessageResponse
    chat: ChatResponse


# Admin Models
class AdminUserResponse(BaseModel):
    """Admin user response with additional info"""
    id: str
    username: str
    email: EmailStr
    full_name: str
    status: UserStatus
    is_active: bool
    is_verified: bool
    message_count: int
    chat_count: int
    friend_count: int
    created_at: datetime
    last_seen: datetime


class AdminChatResponse(BaseModel):
    """Admin chat response with statistics"""
    id: str
    type: ChatType
    name: Optional[str]
    participant_count: int
    message_count: int
    created_by: str
    created_at: datetime
    last_message_at: Optional[datetime]
    is_archived: bool


class AdminStatsResponse(BaseModel):
    """Admin statistics response"""
    total_users: int
    active_users: int
    total_chats: int
    total_messages: int
    messages_today: int
    new_users_today: int
    top_users: List[Dict[str, Any]]
    top_chats: List[Dict[str, Any]]


class AdminUserActionRequest(BaseModel):
    """Admin user action request"""
    action: str = Field(..., pattern="^(ban|unban|verify|unverify|activate|deactivate)$")
    reason: Optional[str] = None


# File Upload Models
class FileUploadResponse(BaseModel):
    """File upload response"""
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    thumbnail_url: Optional[str] = None


# Pagination Models
class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    pagination: PaginationInfo


# Error Models
class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = "validation_error"
    message: str = "Validation failed"
    details: List[Dict[str, Any]]


# Message Models
class MessageSendRequest(BaseModel):
    """Message send request"""
    chat_id: str
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: Optional[str] = "text"
    reply_to_message_id: Optional[str] = None


class MessageUpdateRequest(BaseModel):
    """Message update request"""
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    content: Optional[str]
    message_type: str
    media: Optional[MessageMediaResponse] = None
    chat_id: str
    sender_id: str
    sender_username: str
    sender_full_name: str
    sender_avatar_url: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    status: str
    is_edited: bool
    edited_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime