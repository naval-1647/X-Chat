"""
User repository for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.database.schemas import User, UserStatus
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with specific user operations"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.get_by_field("username", username.lower())
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_by_field("email", email.lower())
    
    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email"""
        user = await self.get_by_username(identifier)
        if not user:
            user = await self.get_by_email(identifier)
        return user
    
    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        **kwargs
    ) -> User:
        """Create a new user"""
        user_data = {
            "username": username.lower(),
            "email": email.lower(),
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            **kwargs
        }
        return await self.create(**user_data)
    
    async def update_last_seen(self, user_id: str, status: UserStatus = UserStatus.OFFLINE) -> bool:
        """Update user's last seen timestamp and status"""
        update_data = {
            "last_seen": datetime.utcnow(),
            "status": status
        }
        user = await self.update_by_id(user_id, **update_data)
        return user is not None
    
    async def update_status(self, user_id: str, status: UserStatus) -> bool:
        """Update user's online status"""
        user = await self.update_by_id(user_id, status=status)
        return user is not None
    
    async def add_friend(self, user_id: str, friend_id: str) -> bool:
        """Add friend to user's friend list"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(friend_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        friend_obj_id = ObjectId(friend_id)
        if friend_obj_id not in user.friends:
            user.friends.append(friend_obj_id)
            user.updated_at = datetime.utcnow()
            await user.save()
        
        return True
    
    async def remove_friend(self, user_id: str, friend_id: str) -> bool:
        """Remove friend from user's friend list"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(friend_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        friend_obj_id = ObjectId(friend_id)
        if friend_obj_id in user.friends:
            user.friends.remove(friend_obj_id)
            user.updated_at = datetime.utcnow()
            await user.save()
        
        return True
    
    async def block_user(self, user_id: str, blocked_user_id: str) -> bool:
        """Block a user"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(blocked_user_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        blocked_obj_id = ObjectId(blocked_user_id)
        if blocked_obj_id not in user.blocked_users:
            user.blocked_users.append(blocked_obj_id)
            # Also remove from friends if they were friends
            if blocked_obj_id in user.friends:
                user.friends.remove(blocked_obj_id)
            user.updated_at = datetime.utcnow()
            await user.save()
        
        return True
    
    async def unblock_user(self, user_id: str, blocked_user_id: str) -> bool:
        """Unblock a user"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(blocked_user_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        blocked_obj_id = ObjectId(blocked_user_id)
        if blocked_obj_id in user.blocked_users:
            user.blocked_users.remove(blocked_obj_id)
            user.updated_at = datetime.utcnow()
            await user.save()
        
        return True
    
    async def is_blocked(self, user_id: str, other_user_id: str) -> bool:
        """Check if user is blocked by another user"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(other_user_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        return ObjectId(other_user_id) in user.blocked_users
    
    async def are_friends(self, user_id: str, other_user_id: str) -> bool:
        """Check if two users are friends"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(other_user_id):
            return False
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        return ObjectId(other_user_id) in user.friends
    
    async def get_friends(self, user_id: str) -> List[User]:
        """Get user's friends"""
        user = await self.get_by_id(user_id)
        if not user or not user.friends:
            return []
        
        friends = await User.find({"_id": {"$in": user.friends}}).to_list()
        return friends
    
    async def get_blocked_users(self, user_id: str) -> List[User]:
        """Get user's blocked users"""
        user = await self.get_by_id(user_id)
        if not user or not user.blocked_users:
            return []
        
        blocked_users = await User.find({"_id": {"$in": user.blocked_users}}).to_list()
        return blocked_users
    
    async def search_users(
        self,
        query: str,
        current_user_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search users by username, email, or name"""
        filter_dict = {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True
        }
        
        # Exclude current user and blocked users
        if current_user_id and ObjectId.is_valid(current_user_id):
            current_user = await self.get_by_id(current_user_id)
            excluded_ids = [ObjectId(current_user_id)]
            
            if current_user and current_user.blocked_users:
                excluded_ids.extend(current_user.blocked_users)
            
            filter_dict["_id"] = {"$nin": excluded_ids}
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="username",
            sort_direction=ASCENDING,
            page=page,
            limit=limit
        )
    
    async def get_online_users(self, limit: int = 100) -> List[User]:
        """Get currently online users"""
        return await User.find(
            {"status": {"$in": [UserStatus.ONLINE, UserStatus.AWAY, UserStatus.BUSY]}}
        ).limit(limit).to_list()
    
    async def get_recently_active_users(self, days: int = 7, limit: int = 100) -> List[User]:
        """Get users active within specified days"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return await User.find(
            {"last_seen": {"$gte": since_date}}
        ).sort([("last_seen", DESCENDING)]).limit(limit).to_list()
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        if not ObjectId.is_valid(user_id):
            return {}
        
        # Get user
        user = await self.get_by_id(user_id)
        if not user:
            return {}
        
        # Use aggregation to get statistics
        pipeline = [
            {"$match": {"_id": ObjectId(user_id)}},
            {
                "$lookup": {
                    "from": "messages",
                    "localField": "_id",
                    "foreignField": "sender_id",
                    "as": "sent_messages"
                }
            },
            {
                "$lookup": {
                    "from": "chats",
                    "localField": "_id",
                    "foreignField": "participants.user_id",
                    "as": "chats"
                }
            },
            {
                "$project": {
                    "username": 1,
                    "full_name": {"$concat": ["$first_name", " ", "$last_name"]},
                    "created_at": 1,
                    "last_seen": 1,
                    "status": 1,
                    "friends_count": {"$size": "$friends"},
                    "blocked_users_count": {"$size": "$blocked_users"},
                    "messages_sent": {"$size": "$sent_messages"},
                    "chats_count": {"$size": "$chats"},
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}
    
    async def update_profile(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """Update user profile"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update basic fields
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        
        # Update profile fields
        if bio is not None:
            user.profile.bio = bio
        if phone is not None:
            user.profile.phone = phone
        if location is not None:
            user.profile.location = location
        if avatar_url is not None:
            user.profile.avatar_url = avatar_url
        
        user.updated_at = datetime.utcnow()
        await user.save()
        return user
    
    async def update_privacy_settings(
        self,
        user_id: str,
        **settings
    ) -> Optional[User]:
        """Update user privacy settings"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update privacy settings
        for key, value in settings.items():
            if hasattr(user.privacy_settings, key):
                setattr(user.privacy_settings, key, value)
        
        user.updated_at = datetime.utcnow()
        await user.save()
        return user
    
    async def update_notification_settings(
        self,
        user_id: str,
        **settings
    ) -> Optional[User]:
        """Update user notification settings"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update notification settings
        for key, value in settings.items():
            if hasattr(user.notification_settings, key):
                setattr(user.notification_settings, key, value)
        
        user.updated_at = datetime.utcnow()
        await user.save()
        return user
    
    async def verify_user(self, user_id: str) -> bool:
        """Mark user as verified"""
        user = await self.update_by_id(user_id, is_verified=True)
        return user is not None
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user = await self.update_by_id(user_id, is_active=False, status=UserStatus.OFFLINE)
        return user is not None
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account"""
        user = await self.update_by_id(user_id, is_active=True)
        return user is not None