"""
Database schemas for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator
from beanie import Document, Indexed
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2

    Compatibility notes:
    - Pydantic v2 may call validator with additional context/arguments. Make
      the validator tolerant of extra parameters to avoid TypeError when Beanie
      / Pydantic invoke it.
    """
    # Use a module-level validator function (see below) to avoid issues with
    # bound-method signatures when pydantic/beanie call validators with extra
    # context arguments.
    @classmethod
    def __get_validators__(cls):
        yield _pyobjectid_validate

    @classmethod
    def __get_pydantic_json_schema__(cls, _field_schema, _handler):
        # Provide a simple JSON schema for documentation/serialization
        return {"type": "string"}


# Module-level validator to ensure signature compatibility with pydantic v2
def _pyobjectid_validate(v, *args, **kwargs):
    # Accept extra args/kwargs (pydantic may pass validation info/context)
    if not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return ObjectId(v)


class UserStatus(str, Enum):
    """User online status"""
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class MessageType(str, Enum):
    """Message types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    VOICE_NOTE = "voice_note"
    LOCATION = "location"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    SEEN = "seen"
    FAILED = "failed"


class ChatType(str, Enum):
    """Chat room types"""
    PRIVATE = "private"
    GROUP = "group"


class FriendRequestStatus(str, Enum):
    """Friend request status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class NotificationType(str, Enum):
    """Notification types"""
    MESSAGE = "message"
    FRIEND_REQUEST = "friend_request"
    MENTION = "mention"
    CHAT_INVITE = "chat_invite"
    SYSTEM = "system"


# User Profile Schema
class UserProfile(BaseModel):
    """User profile information"""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    location: Optional[str] = None


class PrivacySettings(BaseModel):
    """User privacy settings"""
    show_last_seen: bool = True
    show_profile_photo: bool = True
    allow_friend_requests: bool = True
    show_online_status: bool = True


class NotificationSettings(BaseModel):
    """User notification preferences"""
    push_notifications: bool = True
    email_notifications: bool = True
    message_notifications: bool = True
    friend_request_notifications: bool = True
    mention_notifications: bool = True


# Main User Document
class User(Document):
    """User document schema"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., unique=True)
    email: EmailStr = Field(..., unique=True)
    password_hash: str
    
    # Profile information
    first_name: str
    last_name: str
    profile: UserProfile = Field(default_factory=UserProfile)
    
    # Status and presence
    status: UserStatus = UserStatus.OFFLINE
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_verified: bool = False
    
    # Settings
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings)
    
    # Social connections
    friends: List[PyObjectId] = Field(default_factory=list)
    blocked_users: List[PyObjectId] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            "created_at",
            [("username", 1), ("email", 1)],
        ]
    
    @validator("username")
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError("Username must be between 3 and 20 characters")
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v.lower()
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()


# Chat Participant Schema
class ChatParticipant(BaseModel):
    """Chat participant information"""
    user_id: PyObjectId
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: bool = False
    is_muted: bool = False
    last_read_message_id: Optional[PyObjectId] = None
    last_read_at: Optional[datetime] = None


# Chat Room Document
class Chat(Document):
    """Chat room document schema"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Chat information
    type: ChatType
    name: Optional[str] = None  # Group name, None for private chats
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Participants
    participants: List[ChatParticipant] = Field(default_factory=list)
    created_by: PyObjectId
    
    # Settings
    is_archived: bool = False
    is_pinned: bool = False
    auto_delete_messages: Optional[int] = None  # Auto-delete after X days
    
    # Statistics
    message_count: int = 0
    last_message_id: Optional[PyObjectId] = None
    last_message_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chats"
        indexes = [
            "type",
            "created_by",
            "participants.user_id",
            "created_at",
            "last_message_at",
        ]
    
    def get_participant(self, user_id: PyObjectId) -> Optional[ChatParticipant]:
        """Get participant by user ID"""
        for participant in self.participants:
            if participant.user_id == user_id:
                return participant
        return None
    
    def is_participant(self, user_id: PyObjectId) -> bool:
        """Check if user is a participant"""
        return any(p.user_id == user_id for p in self.participants)
    
    def is_admin(self, user_id: PyObjectId) -> bool:
        """Check if user is an admin"""
        participant = self.get_participant(user_id)
        return participant.is_admin if participant else False


# Message Reaction Schema
class MessageReaction(BaseModel):
    """Message reaction information"""
    emoji: str
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Message Media Schema
class MessageMedia(BaseModel):
    """Message media attachment"""
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # For audio/video in seconds
    dimensions: Optional[Dict[str, int]] = None  # {"width": 800, "height": 600}


# Message Document
class Message(Document):
    """Message document schema"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Message content
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    media: Optional[MessageMedia] = None
    
    # Message metadata
    chat_id: PyObjectId
    sender_id: PyObjectId
    
    # Reply/Forward information
    reply_to_message_id: Optional[PyObjectId] = None
    forwarded_from_user_id: Optional[PyObjectId] = None
    forwarded_from_chat_id: Optional[PyObjectId] = None
    
    # Message status and reactions
    status: MessageStatus = MessageStatus.SENT
    reactions: List[MessageReaction] = Field(default_factory=list)
    mentions: List[PyObjectId] = Field(default_factory=list)  # Mentioned user IDs
    
    # Edit history
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    original_content: Optional[str] = None
    
    # Delivery tracking
    delivered_to: List[PyObjectId] = Field(default_factory=list)
    seen_by: List[Dict[str, Any]] = Field(default_factory=list)  # [{"user_id": ObjectId, "seen_at": datetime}]
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Auto-delete
    delete_at: Optional[datetime] = None
    
    class Settings:
        name = "messages"
        indexes = [
            "created_at",
            "message_type",
            [("chat_id", 1), ("created_at", -1)],
            [("sender_id", 1), ("created_at", -1)],
        ]
    
    def add_reaction(self, emoji: str, user_id: PyObjectId) -> bool:
        """Add reaction to message"""
        # Remove existing reaction from same user with same emoji
        self.reactions = [r for r in self.reactions if not (r.emoji == emoji and r.user_id == user_id)]
        
        # Add new reaction
        self.reactions.append(MessageReaction(emoji=emoji, user_id=user_id))
        return True
    
    def remove_reaction(self, emoji: str, user_id: PyObjectId) -> bool:
        """Remove reaction from message"""
        original_count = len(self.reactions)
        self.reactions = [r for r in self.reactions if not (r.emoji == emoji and r.user_id == user_id)]
        return len(self.reactions) < original_count
    
    def mark_as_seen(self, user_id: PyObjectId):
        """Mark message as seen by user"""
        # Remove existing seen record for this user
        self.seen_by = [s for s in self.seen_by if s.get("user_id") != user_id]
        
        # Add new seen record
        self.seen_by.append({
            "user_id": user_id,
            "seen_at": datetime.utcnow()
        })


# Friend Request Document
class FriendRequest(Document):
    """Friend request document schema"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    sender_id: PyObjectId
    receiver_id: PyObjectId
    status: FriendRequestStatus = FriendRequestStatus.PENDING
    message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    
    class Settings:
        name = "friend_requests"
        indexes = [
            "status",
            "created_at",
            [("sender_id", 1), ("receiver_id", 1)],
        ]


# Notification Document
class Notification(Document):
    """Notification document schema"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Notification details
    user_id: PyObjectId
    type: NotificationType
    title: str
    message: str
    
    # Related data
    related_user_id: Optional[PyObjectId] = None
    related_chat_id: Optional[PyObjectId] = None
    related_message_id: Optional[PyObjectId] = None
    
    # Notification state
    is_read: bool = False
    is_sent: bool = False
    
    # Additional data
    data: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    class Settings:
        name = "notifications"
        indexes = [
            "type",
            "is_read",
            "created_at",
            [("user_id", 1), ("is_read", 1)],
            [("user_id", 1), ("created_at", -1)],
        ]


# Blocked User Document
class BlockedUser(Document):
    """Blocked user relationship document"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    blocker_id: PyObjectId  # User who blocked
    blocked_id: PyObjectId  # User who was blocked
    reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "blocked_users"
        indexes = [
            [("blocker_id", 1), ("blocked_id", 1)],
        ]