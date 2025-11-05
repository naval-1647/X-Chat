"""
Database package for ChatX API
"""

from .schemas import *
from .__init__db import (
    init_database,
    close_database,
    get_mongodb_client,
    get_redis_client,
    get_redis_async_client,
    db_manager,
    redis_manager,
    create_admin_user,
    check_mongodb_health,
    check_redis_health,
    get_database_stats,
)

__all__ = [
    # Database models
    "User",
    "Chat",
    "Message",
    "FriendRequest",
    "Notification",
    "BlockedUser",
    "MessageType",
    "MessageStatus",
    "ChatType",
    "UserStatus",
    "FriendRequestStatus",
    "NotificationType",
    
    # Request/Response models
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    "ChatCreateRequest",
    "MessageSendRequest",
    "MessageResponse",
    "FriendRequestResponse",
    "NotificationResponse",
    
    # Database functions
    "init_database",
    "close_database",
    "get_mongodb_client",
    "get_redis_client",
    "get_redis_async_client",
    "db_manager",
    "redis_manager",
    "create_admin_user",
    "check_mongodb_health",
    "check_redis_health",
    "get_database_stats",
]