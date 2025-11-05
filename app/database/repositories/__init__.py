"""
Database repositories for ChatX API
"""

from .base import BaseRepository
from .user_repository import UserRepository
from .chat_repository import ChatRepository
from .message_repository import MessageRepository
from .notification_repository import NotificationRepository
from .friend_request_repository import FriendRequestRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ChatRepository",
    "MessageRepository",
    "NotificationRepository",
    "FriendRequestRepository",
]


# Repository instances (can be used as singletons)
user_repo = UserRepository()
chat_repo = ChatRepository()
message_repo = MessageRepository()
notification_repo = NotificationRepository()
friend_request_repo = FriendRequestRepository()