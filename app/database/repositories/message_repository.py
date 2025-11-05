"""
Message repository for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import DESCENDING, ASCENDING

from app.database.schemas import Message, MessageType, MessageStatus, MessageReaction, MessageMedia
from app.database.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Message repository with specific message operations"""
    
    def __init__(self):
        super().__init__(Message)
    
    async def create_message(
        self,
        content: Optional[str],
        chat_id: str,
        sender_id: str,
        message_type: MessageType = MessageType.TEXT,
        reply_to_message_id: Optional[str] = None,
        media: Optional[Dict[str, Any]] = None,
        mentions: Optional[List[str]] = None
    ) -> Optional[Message]:
        """Create a new message"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(sender_id):
            return None
        
        message_data = {
            "content": content,
            "chat_id": ObjectId(chat_id),
            "sender_id": ObjectId(sender_id),
            "message_type": message_type,
            "media": media,
        }
        
        if reply_to_message_id and ObjectId.is_valid(reply_to_message_id):
            message_data["reply_to_message_id"] = ObjectId(reply_to_message_id)
        
        if mentions:
            valid_mentions = [ObjectId(uid) for uid in mentions if ObjectId.is_valid(uid)]
            message_data["mentions"] = valid_mentions
        
        return await self.create(**message_data)
    
    async def get_chat_messages(
        self,
        chat_id: str,
        page: int = 1,
        limit: int = 50,
        before_message_id: Optional[str] = None,
        after_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get messages for a chat with pagination"""
        if not ObjectId.is_valid(chat_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {"chat_id": ObjectId(chat_id)}
        
        # Add time-based filtering
        if before_message_id and ObjectId.is_valid(before_message_id):
            before_message = await self.get_by_id(before_message_id)
            if before_message:
                filter_dict["created_at"] = {"$lt": before_message.created_at}
        
        if after_message_id and ObjectId.is_valid(after_message_id):
            after_message = await self.get_by_id(after_message_id)
            if after_message:
                filter_dict["created_at"] = filter_dict.get("created_at", {})
                filter_dict["created_at"]["$gt"] = after_message.created_at
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def update_message_content(
        self,
        message_id: str,
        new_content: str,
        user_id: str
    ) -> Optional[Message]:
        """Update message content (edit message)"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return None
        
        message = await self.get_by_id(message_id)
        if not message or message.sender_id != ObjectId(user_id):
            return None
        
        # Store original content if not already edited
        if not message.is_edited:
            message.original_content = message.content
        
        # Update message
        message.content = new_content
        message.is_edited = True
        message.edited_at = datetime.utcnow()
        message.updated_at = datetime.utcnow()
        
        await message.save()
        return message
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (soft delete by clearing content)"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message or message.sender_id != ObjectId(user_id):
            return False
        
        # Soft delete - clear content and mark as system type
        message.content = "This message was deleted"
        message.message_type = MessageType.SYSTEM
        message.media = None
        message.updated_at = datetime.utcnow()
        
        await message.save()
        return True
    
    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Add reaction to message"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message:
            return False
        
        user_obj_id = ObjectId(user_id)
        
        # Remove existing reaction from same user with same emoji
        message.reactions = [
            r for r in message.reactions 
            if not (r.emoji == emoji and r.user_id == user_obj_id)
        ]
        
        # Add new reaction
        message.reactions.append(MessageReaction(emoji=emoji, user_id=user_obj_id))
        message.updated_at = datetime.utcnow()
        
        await message.save()
        return True
    
    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Remove reaction from message"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message:
            return False
        
        user_obj_id = ObjectId(user_id)
        original_count = len(message.reactions)
        
        # Remove reaction
        message.reactions = [
            r for r in message.reactions 
            if not (r.emoji == emoji and r.user_id == user_obj_id)
        ]
        
        if len(message.reactions) < original_count:
            message.updated_at = datetime.utcnow()
            await message.save()
            return True
        
        return False
    
    async def mark_as_delivered(self, message_id: str, user_id: str) -> bool:
        """Mark message as delivered to user"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message:
            return False
        
        user_obj_id = ObjectId(user_id)
        
        # Add to delivered list if not already there
        if user_obj_id not in message.delivered_to:
            message.delivered_to.append(user_obj_id)
            message.updated_at = datetime.utcnow()
            await message.save()
        
        return True
    
    async def mark_as_seen(self, message_id: str, user_id: str) -> bool:
        """Mark message as seen by user"""
        if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message:
            return False
        
        user_obj_id = ObjectId(user_id)
        
        # Remove existing seen record for this user
        message.seen_by = [s for s in message.seen_by if s.get("user_id") != user_obj_id]
        
        # Add new seen record
        message.seen_by.append({
            "user_id": user_obj_id,
            "seen_at": datetime.utcnow()
        })
        
        message.updated_at = datetime.utcnow()
        await message.save()
        return True
    
    async def get_unread_messages(self, chat_id: str, user_id: str) -> List[Message]:
        """Get unread messages for user in chat"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(user_id):
            return []
        
        user_obj_id = ObjectId(user_id)
        
        # Find messages where user hasn't seen them and user is not the sender
        messages = await Message.find({
            "chat_id": ObjectId(chat_id),
            "sender_id": {"$ne": user_obj_id},
            "seen_by.user_id": {"$ne": user_obj_id}
        }).sort([("created_at", ASCENDING)]).to_list()
        
        return messages
    
    async def get_unread_count(self, chat_id: str, user_id: str) -> int:
        """Get count of unread messages for user in chat"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(user_id):
            return 0
        
        user_obj_id = ObjectId(user_id)
        
        count = await Message.find({
            "chat_id": ObjectId(chat_id),
            "sender_id": {"$ne": user_obj_id},
            "seen_by.user_id": {"$ne": user_obj_id}
        }).count()
        
        return count
    
    async def search_messages(
        self,
        chat_id: str,
        query: str,
        message_type: Optional[MessageType] = None,
        sender_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search messages in chat"""
        if not ObjectId.is_valid(chat_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "chat_id": ObjectId(chat_id),
            "content": {"$regex": query, "$options": "i"}
        }
        
        if message_type:
            filter_dict["message_type"] = message_type
        
        if sender_id and ObjectId.is_valid(sender_id):
            filter_dict["sender_id"] = ObjectId(sender_id)
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            filter_dict["created_at"] = date_filter
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def get_media_messages(
        self,
        chat_id: str,
        media_type: Optional[MessageType] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get media messages from chat"""
        if not ObjectId.is_valid(chat_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "chat_id": ObjectId(chat_id),
            "message_type": {"$ne": MessageType.TEXT}
        }
        
        if media_type and media_type != MessageType.TEXT:
            filter_dict["message_type"] = media_type
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def get_messages_with_mentions(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get messages where user is mentioned"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "mentions": ObjectId(user_id)
        }
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def get_message_statistics(self, chat_id: str) -> Dict[str, Any]:
        """Get message statistics for chat"""
        if not ObjectId.is_valid(chat_id):
            return {}
        
        pipeline = [
            {"$match": {"chat_id": ObjectId(chat_id)}},
            {
                "$group": {
                    "_id": None,
                    "total_messages": {"$sum": 1},
                    "text_messages": {
                        "$sum": {"$cond": [{"$eq": ["$message_type", "text"]}, 1, 0]}
                    },
                    "media_messages": {
                        "$sum": {"$cond": [{"$ne": ["$message_type", "text"]}, 1, 0]}
                    },
                    "messages_today": {
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
                    },
                    "total_reactions": {"$sum": {"$size": "$reactions"}},
                    "most_active_hour": {
                        "$push": {"$hour": "$created_at"}
                    }
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}
    
    async def get_user_message_stats(self, user_id: str) -> Dict[str, Any]:
        """Get message statistics for user"""
        if not ObjectId.is_valid(user_id):
            return {}
        
        pipeline = [
            {"$match": {"sender_id": ObjectId(user_id)}},
            {
                "$group": {
                    "_id": None,
                    "total_messages": {"$sum": 1},
                    "text_messages": {
                        "$sum": {"$cond": [{"$eq": ["$message_type", "text"]}, 1, 0]}
                    },
                    "media_messages": {
                        "$sum": {"$cond": [{"$ne": ["$message_type", "text"]}, 1, 0]}
                    },
                    "messages_today": {
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
                    },
                    "reactions_received": {"$sum": {"$size": "$reactions"}},
                    "avg_message_length": {"$avg": {"$strLenCP": "$content"}}
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}
    
    async def delete_old_messages(self, days: int = 30) -> int:
        """Delete messages older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find messages to delete
        old_messages = await Message.find({
            "created_at": {"$lt": cutoff_date}
        }).to_list()
        
        if old_messages:
            # Delete messages
            await Message.find({
                "created_at": {"$lt": cutoff_date}
            }).delete()
            
            return len(old_messages)
        
        return 0
    
    async def forward_message(
        self,
        original_message_id: str,
        target_chat_id: str,
        sender_id: str
    ) -> Optional[Message]:
        """Forward a message to another chat"""
        if not all(ObjectId.is_valid(id_) for id_ in [original_message_id, target_chat_id, sender_id]):
            return None
        
        original_message = await self.get_by_id(original_message_id)
        if not original_message:
            return None
        
        # Create forwarded message
        forwarded_data = {
            "content": original_message.content,
            "message_type": original_message.message_type,
            "media": original_message.media,
            "chat_id": ObjectId(target_chat_id),
            "sender_id": ObjectId(sender_id),
            "forwarded_from_user_id": original_message.sender_id,
            "forwarded_from_chat_id": original_message.chat_id,
        }
        
        return await self.create(**forwarded_data)
    
    async def set_auto_delete(self, message_id: str, delete_after_hours: int) -> bool:
        """Set auto-delete timer for message"""
        if not ObjectId.is_valid(message_id):
            return False
        
        message = await self.get_by_id(message_id)
        if not message:
            return False
        
        delete_at = datetime.utcnow() + timedelta(hours=delete_after_hours)
        message.delete_at = delete_at
        message.updated_at = datetime.utcnow()
        
        await message.save()
        return True
    
    async def cleanup_expired_messages(self) -> int:
        """Delete messages that have expired (auto-delete)"""
        now = datetime.utcnow()
        
        # Find expired messages
        expired_messages = await Message.find({
            "delete_at": {"$lte": now}
        }).to_list()
        
        if expired_messages:
            # Delete expired messages
            await Message.find({
                "delete_at": {"$lte": now}
            }).delete()
            
            return len(expired_messages)
        
        return 0