"""
Notification repository for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import DESCENDING

from app.database.schemas import Notification, NotificationType
from app.database.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Notification repository with specific notification operations"""
    
    def __init__(self):
        super().__init__(Notification)
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_user_id: Optional[str] = None,
        related_chat_id: Optional[str] = None,
        related_message_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """Create a new notification"""
        if not ObjectId.is_valid(user_id):
            return None
        
        notification_data = {
            "user_id": ObjectId(user_id),
            "type": notification_type,
            "title": title,
            "message": message,
            "data": data or {}
        }
        
        # Add related IDs if provided and valid
        if related_user_id and ObjectId.is_valid(related_user_id):
            notification_data["related_user_id"] = ObjectId(related_user_id)
        
        if related_chat_id and ObjectId.is_valid(related_chat_id):
            notification_data["related_chat_id"] = ObjectId(related_chat_id)
        
        if related_message_id and ObjectId.is_valid(related_message_id):
            notification_data["related_message_id"] = ObjectId(related_message_id)
        
        return await self.create(**notification_data)
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get notifications for a user"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {"user_id": ObjectId(user_id)}
        
        if unread_only:
            filter_dict["is_read"] = False
        
        if notification_type:
            filter_dict["type"] = notification_type
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        if not ObjectId.is_valid(notification_id) or not ObjectId.is_valid(user_id):
            return False
        
        notification = await self.get_by_id(notification_id)
        if not notification or notification.user_id != ObjectId(user_id):
            return False
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            notification.updated_at = datetime.utcnow()
            await notification.save()
        
        return True
    
    async def mark_multiple_as_read(self, notification_ids: List[str], user_id: str) -> int:
        """Mark multiple notifications as read"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        valid_ids = [ObjectId(nid) for nid in notification_ids if ObjectId.is_valid(nid)]
        if not valid_ids:
            return 0
        
        # Update notifications
        result = await self.collection.update_many(
            {
                "_id": {"$in": valid_ids},
                "user_id": ObjectId(user_id),
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        result = await self.collection.update_many(
            {
                "user_id": ObjectId(user_id),
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for user"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        return await self.count({
            "user_id": ObjectId(user_id),
            "is_read": False
        })
    
    async def get_unread_count_by_type(self, user_id: str) -> Dict[str, int]:
        """Get unread count grouped by notification type"""
        if not ObjectId.is_valid(user_id):
            return {}
        
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "is_read": False
                }
            },
            {
                "$group": {
                    "_id": "$type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return {item["_id"]: item["count"] for item in result}
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        if not ObjectId.is_valid(notification_id) or not ObjectId.is_valid(user_id):
            return False
        
        notification = await self.get_by_id(notification_id)
        if not notification or notification.user_id != ObjectId(user_id):
            return False
        
        await notification.delete()
        return True
    
    async def delete_multiple_notifications(self, notification_ids: List[str], user_id: str) -> int:
        """Delete multiple notifications"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        valid_ids = [ObjectId(nid) for nid in notification_ids if ObjectId.is_valid(nid)]
        if not valid_ids:
            return 0
        
        result = await self.collection.delete_many({
            "_id": {"$in": valid_ids},
            "user_id": ObjectId(user_id)
        })
        
        return result.deleted_count
    
    async def delete_old_notifications(self, user_id: str, days: int = 30) -> int:
        """Delete old notifications for user"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.collection.delete_many({
            "user_id": ObjectId(user_id),
            "created_at": {"$lt": cutoff_date}
        })
        
        return result.deleted_count
    
    async def create_message_notification(
        self,
        recipient_id: str,
        sender_id: str,
        chat_id: str,
        message_id: str,
        message_content: str,
        chat_name: Optional[str] = None
    ) -> Optional[Notification]:
        """Create notification for new message"""
        if not all(ObjectId.is_valid(id_) for id_ in [recipient_id, sender_id, chat_id, message_id]):
            return None
        
        # Get sender info for notification
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        sender = await user_repo.get_by_id(sender_id)
        
        if not sender:
            return None
        
        title = f"New message from {sender.full_name}"
        if chat_name:
            title = f"New message in {chat_name}"
        
        # Truncate message content for notification
        truncated_content = message_content[:100] + "..." if len(message_content) > 100 else message_content
        
        return await self.create_notification(
            user_id=recipient_id,
            notification_type=NotificationType.MESSAGE,
            title=title,
            message=truncated_content,
            related_user_id=sender_id,
            related_chat_id=chat_id,
            related_message_id=message_id,
            data={
                "sender_username": sender.username,
                "sender_full_name": sender.full_name,
                "chat_name": chat_name
            }
        )
    
    async def create_friend_request_notification(
        self,
        recipient_id: str,
        sender_id: str,
        friend_request_id: str,
        message: Optional[str] = None
    ) -> Optional[Notification]:
        """Create notification for friend request"""
        if not all(ObjectId.is_valid(id_) for id_ in [recipient_id, sender_id, friend_request_id]):
            return None
        
        # Get sender info
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        sender = await user_repo.get_by_id(sender_id)
        
        if not sender:
            return None
        
        title = f"Friend request from {sender.full_name}"
        notification_message = message or f"{sender.full_name} wants to be your friend"
        
        return await self.create_notification(
            user_id=recipient_id,
            notification_type=NotificationType.FRIEND_REQUEST,
            title=title,
            message=notification_message,
            related_user_id=sender_id,
            data={
                "sender_username": sender.username,
                "sender_full_name": sender.full_name,
                "friend_request_id": friend_request_id,
                "request_message": message
            }
        )
    
    async def create_mention_notification(
        self,
        mentioned_user_id: str,
        sender_id: str,
        chat_id: str,
        message_id: str,
        message_content: str,
        chat_name: Optional[str] = None
    ) -> Optional[Notification]:
        """Create notification for mention"""
        if not all(ObjectId.is_valid(id_) for id_ in [mentioned_user_id, sender_id, chat_id, message_id]):
            return None
        
        # Get sender info
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        sender = await user_repo.get_by_id(sender_id)
        
        if not sender:
            return None
        
        title = f"You were mentioned by {sender.full_name}"
        if chat_name:
            title = f"You were mentioned in {chat_name}"
        
        # Truncate message content
        truncated_content = message_content[:100] + "..." if len(message_content) > 100 else message_content
        
        return await self.create_notification(
            user_id=mentioned_user_id,
            notification_type=NotificationType.MENTION,
            title=title,
            message=truncated_content,
            related_user_id=sender_id,
            related_chat_id=chat_id,
            related_message_id=message_id,
            data={
                "sender_username": sender.username,
                "sender_full_name": sender.full_name,
                "chat_name": chat_name
            }
        )
    
    async def create_chat_invite_notification(
        self,
        invited_user_id: str,
        inviter_id: str,
        chat_id: str,
        chat_name: str
    ) -> Optional[Notification]:
        """Create notification for chat invitation"""
        if not all(ObjectId.is_valid(id_) for id_ in [invited_user_id, inviter_id, chat_id]):
            return None
        
        # Get inviter info
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        inviter = await user_repo.get_by_id(inviter_id)
        
        if not inviter:
            return None
        
        title = f"Invited to {chat_name}"
        message = f"{inviter.full_name} invited you to join {chat_name}"
        
        return await self.create_notification(
            user_id=invited_user_id,
            notification_type=NotificationType.CHAT_INVITE,
            title=title,
            message=message,
            related_user_id=inviter_id,
            related_chat_id=chat_id,
            data={
                "inviter_username": inviter.username,
                "inviter_full_name": inviter.full_name,
                "chat_name": chat_name
            }
        )
    
    async def get_notification_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for user"""
        if not ObjectId.is_valid(user_id):
            return {}
        
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {
                "$group": {
                    "_id": None,
                    "total_notifications": {"$sum": 1},
                    "unread_notifications": {
                        "$sum": {"$cond": [{"$eq": ["$is_read", False]}, 1, 0]}
                    },
                    "message_notifications": {
                        "$sum": {"$cond": [{"$eq": ["$type", "message"]}, 1, 0]}
                    },
                    "friend_request_notifications": {
                        "$sum": {"$cond": [{"$eq": ["$type", "friend_request"]}, 1, 0]}
                    },
                    "mention_notifications": {
                        "$sum": {"$cond": [{"$eq": ["$type", "mention"]}, 1, 0]}
                    },
                    "notifications_today": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$gte": [
                                        "$created_at",
                                        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}