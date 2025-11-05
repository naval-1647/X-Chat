"""
Chat repository for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING

from app.database.schemas import Chat, ChatType, ChatParticipant
from app.database.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """Chat repository with specific chat operations"""
    
    def __init__(self):
        super().__init__(Chat)
    
    async def create_private_chat(self, user1_id: str, user2_id: str) -> Optional[Chat]:
        """Create a private chat between two users"""
        if not ObjectId.is_valid(user1_id) or not ObjectId.is_valid(user2_id):
            return None
        
        # Check if private chat already exists
        existing_chat = await self.get_private_chat(user1_id, user2_id)
        if existing_chat:
            return existing_chat
        
        # Create participants
        participants = [
            ChatParticipant(user_id=ObjectId(user1_id)),
            ChatParticipant(user_id=ObjectId(user2_id))
        ]
        
        # Create chat
        chat_data = {
            "type": ChatType.PRIVATE,
            "participants": participants,
            "created_by": ObjectId(user1_id)
        }
        
        return await self.create(**chat_data)
    
    async def create_group_chat(
        self,
        creator_id: str,
        participant_ids: List[str],
        name: str,
        description: Optional[str] = None
    ) -> Optional[Chat]:
        """Create a group chat"""
        if not ObjectId.is_valid(creator_id):
            return None
        
        # Validate all participant IDs
        valid_participant_ids = []
        for pid in participant_ids:
            if ObjectId.is_valid(pid):
                valid_participant_ids.append(ObjectId(pid))
        
        if not valid_participant_ids:
            return None
        
        # Add creator to participants if not already included
        creator_obj_id = ObjectId(creator_id)
        if creator_obj_id not in valid_participant_ids:
            valid_participant_ids.append(creator_obj_id)
        
        # Create participants (creator is admin)
        participants = []
        for user_id in valid_participant_ids:
            is_admin = user_id == creator_obj_id
            participants.append(ChatParticipant(user_id=user_id, is_admin=is_admin))
        
        # Create chat
        chat_data = {
            "type": ChatType.GROUP,
            "name": name,
            "description": description,
            "participants": participants,
            "created_by": creator_obj_id
        }
        
        return await self.create(**chat_data)
    
    async def get_private_chat(self, user1_id: str, user2_id: str) -> Optional[Chat]:
        """Get private chat between two users"""
        if not ObjectId.is_valid(user1_id) or not ObjectId.is_valid(user2_id):
            return None
        
        user1_obj_id = ObjectId(user1_id)
        user2_obj_id = ObjectId(user2_id)
        
        chat = await Chat.find_one({
            "type": ChatType.PRIVATE,
            "participants.user_id": {"$all": [user1_obj_id, user2_obj_id]},
            "$expr": {"$eq": [{"$size": "$participants"}, 2]}
        })
        
        return chat
    
    async def get_user_chats(
        self,
        user_id: str,
        chat_type: Optional[ChatType] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get chats for a user"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "participants.user_id": ObjectId(user_id)
        }
        
        if chat_type:
            filter_dict["type"] = chat_type
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="last_message_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def add_participant(self, chat_id: str, user_id: str, added_by: str) -> bool:
        """Add participant to chat"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, added_by]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat or chat.type != ChatType.GROUP:
            return False
        
        # Check if user adding has admin rights
        if not chat.is_admin(ObjectId(added_by)):
            return False
        
        # Check if user is already a participant
        user_obj_id = ObjectId(user_id)
        if chat.is_participant(user_obj_id):
            return False
        
        # Add participant
        new_participant = ChatParticipant(user_id=user_obj_id)
        chat.participants.append(new_participant)
        chat.updated_at = datetime.utcnow()
        await chat.save()
        
        return True
    
    async def remove_participant(self, chat_id: str, user_id: str, removed_by: str) -> bool:
        """Remove participant from chat"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, removed_by]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat or chat.type != ChatType.GROUP:
            return False
        
        user_obj_id = ObjectId(user_id)
        removed_by_obj_id = ObjectId(removed_by)
        
        # Check permissions (admin can remove anyone, users can remove themselves)
        if not (chat.is_admin(removed_by_obj_id) or user_obj_id == removed_by_obj_id):
            return False
        
        # Remove participant
        chat.participants = [p for p in chat.participants if p.user_id != user_obj_id]
        chat.updated_at = datetime.utcnow()
        await chat.save()
        
        return True
    
    async def update_participant_role(
        self,
        chat_id: str,
        user_id: str,
        is_admin: bool,
        updated_by: str
    ) -> bool:
        """Update participant admin status"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, updated_by]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat or chat.type != ChatType.GROUP:
            return False
        
        # Check if updater has admin rights
        if not chat.is_admin(ObjectId(updated_by)):
            return False
        
        # Update participant
        user_obj_id = ObjectId(user_id)
        for participant in chat.participants:
            if participant.user_id == user_obj_id:
                participant.is_admin = is_admin
                break
        else:
            return False
        
        chat.updated_at = datetime.utcnow()
        await chat.save()
        return True
    
    async def mute_participant(self, chat_id: str, user_id: str, muted_by: str) -> bool:
        """Mute participant in chat"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, muted_by]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat:
            return False
        
        # Check if muter has admin rights
        if not chat.is_admin(ObjectId(muted_by)):
            return False
        
        # Mute participant
        user_obj_id = ObjectId(user_id)
        for participant in chat.participants:
            if participant.user_id == user_obj_id:
                participant.is_muted = True
                break
        else:
            return False
        
        chat.updated_at = datetime.utcnow()
        await chat.save()
        return True
    
    async def unmute_participant(self, chat_id: str, user_id: str, unmuted_by: str) -> bool:
        """Unmute participant in chat"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, unmuted_by]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat:
            return False
        
        # Check if unmuter has admin rights
        if not chat.is_admin(ObjectId(unmuted_by)):
            return False
        
        # Unmute participant
        user_obj_id = ObjectId(user_id)
        for participant in chat.participants:
            if participant.user_id == user_obj_id:
                participant.is_muted = False
                break
        else:
            return False
        
        chat.updated_at = datetime.utcnow()
        await chat.save()
        return True
    
    async def update_chat_info(
        self,
        chat_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[Chat]:
        """Update chat information"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(user_id):
            return None
        
        chat = await self.get_by_id(chat_id)
        if not chat or chat.type != ChatType.GROUP:
            return None
        
        # Check if user has admin rights
        if not chat.is_admin(ObjectId(user_id)):
            return None
        
        # Update chat info
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
        
        if update_data:
            return await self.update_by_id(chat_id, **update_data)
        
        return chat
    
    async def update_last_message(self, chat_id: str, message_id: str) -> bool:
        """Update chat's last message info"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(message_id):
            return False
        
        update_data = {
            "last_message_id": ObjectId(message_id),
            "last_message_at": datetime.utcnow(),
            "message_count": {"$inc": 1}  # This would need special handling
        }
        
        chat = await self.get_by_id(chat_id)
        if chat:
            chat.last_message_id = ObjectId(message_id)
            chat.last_message_at = datetime.utcnow()
            chat.message_count += 1
            chat.updated_at = datetime.utcnow()
            await chat.save()
            return True
        
        return False
    
    async def update_participant_read_status(
        self,
        chat_id: str,
        user_id: str,
        message_id: str
    ) -> bool:
        """Update participant's last read message"""
        if not all(ObjectId.is_valid(id_) for id_ in [chat_id, user_id, message_id]):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat:
            return False
        
        # Update participant's read status
        user_obj_id = ObjectId(user_id)
        message_obj_id = ObjectId(message_id)
        
        for participant in chat.participants:
            if participant.user_id == user_obj_id:
                participant.last_read_message_id = message_obj_id
                participant.last_read_at = datetime.utcnow()
                break
        else:
            return False
        
        chat.updated_at = datetime.utcnow()
        await chat.save()
        return True
    
    async def archive_chat(self, chat_id: str, user_id: str) -> bool:
        """Archive chat for user (implementation depends on requirements)"""
        # This could be implemented as a user-specific setting
        # For now, we'll mark the chat as archived globally
        chat = await self.update_by_id(chat_id, is_archived=True)
        return chat is not None
    
    async def unarchive_chat(self, chat_id: str, user_id: str) -> bool:
        """Unarchive chat for user"""
        chat = await self.update_by_id(chat_id, is_archived=False)
        return chat is not None
    
    async def pin_chat(self, chat_id: str, user_id: str) -> bool:
        """Pin chat for user"""
        chat = await self.update_by_id(chat_id, is_pinned=True)
        return chat is not None
    
    async def unpin_chat(self, chat_id: str, user_id: str) -> bool:
        """Unpin chat for user"""
        chat = await self.update_by_id(chat_id, is_pinned=False)
        return chat is not None
    
    async def get_chat_participants(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get detailed chat participants info"""
        if not ObjectId.is_valid(chat_id):
            return []
        
        pipeline = [
            {"$match": {"_id": ObjectId(chat_id)}},
            {"$unwind": "$participants"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "participants.user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": "$user_info"},
            {
                "$project": {
                    "user_id": "$participants.user_id",
                    "username": "$user_info.username",
                    "full_name": {
                        "$concat": ["$user_info.first_name", " ", "$user_info.last_name"]
                    },
                    "avatar_url": "$user_info.profile.avatar_url",
                    "joined_at": "$participants.joined_at",
                    "is_admin": "$participants.is_admin",
                    "is_muted": "$participants.is_muted",
                    "last_read_at": "$participants.last_read_at",
                    "status": "$user_info.status",
                    "last_seen": "$user_info.last_seen"
                }
            }
        ]
        
        return await self.aggregate(pipeline)
    
    async def get_chat_statistics(self, chat_id: str) -> Dict[str, Any]:
        """Get chat statistics"""
        if not ObjectId.is_valid(chat_id):
            return {}
        
        pipeline = [
            {"$match": {"_id": ObjectId(chat_id)}},
            {
                "$lookup": {
                    "from": "messages",
                    "localField": "_id",
                    "foreignField": "chat_id",
                    "as": "messages"
                }
            },
            {
                "$project": {
                    "type": 1,
                    "name": 1,
                    "created_at": 1,
                    "participant_count": {"$size": "$participants"},
                    "message_count": {"$size": "$messages"},
                    "last_message_at": 1,
                    "messages_today": {
                        "$size": {
                            "$filter": {
                                "input": "$messages",
                                "cond": {
                                    "$gte": [
                                        "$$this.created_at",
                                        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}
    
    async def search_chats(
        self,
        user_id: str,
        query: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search chats by name or description"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "participants.user_id": ObjectId(user_id),
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="last_message_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def is_participant(self, chat_id: str, user_id: str) -> bool:
        """Check if user is participant of chat"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(user_id):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat:
            return False
        
        user_obj_id = ObjectId(user_id)
        return any(p.user_id == user_obj_id for p in chat.participants)
    
    async def update_last_message(self, chat_id: str, message_id: str) -> bool:
        """Update chat's last message info"""
        if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(message_id):
            return False
        
        chat = await self.get_by_id(chat_id)
        if not chat:
            return False
        
        chat.last_message_at = datetime.utcnow()
        chat.message_count = (chat.message_count or 0) + 1
        chat.updated_at = datetime.utcnow()
        
        await chat.save()
        return True