"""
Friend request repository for ChatX API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import DESCENDING

from app.database.schemas import FriendRequest, FriendRequestStatus
from app.database.repositories.base import BaseRepository


class FriendRequestRepository(BaseRepository[FriendRequest]):
    """Friend request repository with specific friend request operations"""
    
    def __init__(self):
        super().__init__(FriendRequest)
    
    async def create_friend_request(
        self,
        sender_id: str,
        receiver_id: str,
        message: Optional[str] = None
    ) -> Optional[FriendRequest]:
        """Create a new friend request"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 create_friend_request called: sender={sender_id}, receiver={receiver_id}")
        
        if not ObjectId.is_valid(sender_id) or not ObjectId.is_valid(receiver_id):
            logger.error(f"❌ Invalid ObjectIds: sender={sender_id}, receiver={receiver_id}")
            return None
        
        # Check if request already exists
        logger.info("🔍 Checking for existing request...")
        existing_request = await self.get_existing_request(sender_id, receiver_id)
        if existing_request:
            logger.warning(f"❌ Request already exists: {existing_request.id}, status={existing_request.status}")
            return None
        
        logger.info("✅ No existing request found, creating new one...")
        
        request_data = {
            "sender_id": ObjectId(sender_id),
            "receiver_id": ObjectId(receiver_id),
            "message": message,
            "status": FriendRequestStatus.PENDING
        }
        
        try:
            result = await self.create(**request_data)
            if result:
                logger.info(f"✅ Friend request created successfully: {result.id}")
            else:
                logger.error("❌ Failed to create friend request - create() returned None")
            return result
        except Exception as e:
            logger.error(f"❌ Error creating friend request: {str(e)}")
            return None
    
    async def get_existing_request(
        self,
        sender_id: str,
        receiver_id: str
    ) -> Optional[FriendRequest]:
        """Get existing friend request between two users"""
        if not ObjectId.is_valid(sender_id) or not ObjectId.is_valid(receiver_id):
            return None
        
        # Check for request in either direction
        request = await FriendRequest.find_one({
            "$or": [
                {
                    "sender_id": ObjectId(sender_id),
                    "receiver_id": ObjectId(receiver_id)
                },
                {
                    "sender_id": ObjectId(receiver_id),
                    "receiver_id": ObjectId(sender_id)
                }
            ],
            "status": {"$ne": FriendRequestStatus.REJECTED}
        })
        
        return request
    
    async def get_pending_requests_received(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get pending friend requests received by user"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "receiver_id": ObjectId(user_id),
            "status": FriendRequestStatus.PENDING
        }
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def get_pending_requests_sent(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get pending friend requests sent by user"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "sender_id": ObjectId(user_id),
            "status": FriendRequestStatus.PENDING
        }
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def accept_friend_request(
        self,
        request_id: str,
        user_id: str
    ) -> Optional[FriendRequest]:
        """Accept a friend request"""
        if not ObjectId.is_valid(request_id) or not ObjectId.is_valid(user_id):
            return None
        
        friend_request = await self.get_by_id(request_id)
        if not friend_request or friend_request.receiver_id != ObjectId(user_id):
            return None
        
        if friend_request.status != FriendRequestStatus.PENDING:
            return None
        
        # Update request status
        friend_request.status = FriendRequestStatus.ACCEPTED
        friend_request.responded_at = datetime.utcnow()
        friend_request.updated_at = datetime.utcnow()
        await friend_request.save()
        
        # Add friends to each other's friend lists
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        
        await user_repo.add_friend(str(friend_request.sender_id), str(friend_request.receiver_id))
        await user_repo.add_friend(str(friend_request.receiver_id), str(friend_request.sender_id))
        
        return friend_request
    
    async def reject_friend_request(
        self,
        request_id: str,
        user_id: str
    ) -> Optional[FriendRequest]:
        """Reject a friend request"""
        if not ObjectId.is_valid(request_id) or not ObjectId.is_valid(user_id):
            return None
        
        friend_request = await self.get_by_id(request_id)
        if not friend_request or friend_request.receiver_id != ObjectId(user_id):
            return None
        
        if friend_request.status != FriendRequestStatus.PENDING:
            return None
        
        # Update request status
        friend_request.status = FriendRequestStatus.REJECTED
        friend_request.responded_at = datetime.utcnow()
        friend_request.updated_at = datetime.utcnow()
        await friend_request.save()
        
        return friend_request
    
    async def cancel_friend_request(
        self,
        request_id: str,
        user_id: str
    ) -> bool:
        """Cancel a friend request (sender only)"""
        if not ObjectId.is_valid(request_id) or not ObjectId.is_valid(user_id):
            return False
        
        friend_request = await self.get_by_id(request_id)
        if not friend_request or friend_request.sender_id != ObjectId(user_id):
            return False
        
        if friend_request.status != FriendRequestStatus.PENDING:
            return False
        
        # Delete the request
        await friend_request.delete()
        return True
    
    async def get_request_history(
        self,
        user_id: str,
        status: Optional[FriendRequestStatus] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get friend request history for user (both sent and received)"""
        if not ObjectId.is_valid(user_id):
            return {"items": [], "pagination": {}}
        
        filter_dict = {
            "$or": [
                {"sender_id": ObjectId(user_id)},
                {"receiver_id": ObjectId(user_id)}
            ]
        }
        
        if status:
            filter_dict["status"] = status
        
        return await self.find_with_pagination(
            filter_dict=filter_dict,
            sort_field="created_at",
            sort_direction=DESCENDING,
            page=page,
            limit=limit
        )
    
    async def get_requests_with_user_info(
        self,
        user_id: str,
        received: bool = True,
        page: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get friend requests with sender/receiver user information"""
        if not ObjectId.is_valid(user_id):
            return []
        
        # Determine which requests to get (received or sent)
        match_field = "receiver_id" if received else "sender_id"
        lookup_field = "sender_id" if received else "receiver_id"
        
        pipeline = [
            {
                "$match": {
                    match_field: ObjectId(user_id),
                    "status": FriendRequestStatus.PENDING
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": lookup_field,
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": "$user_info"},
            {
                "$project": {
                    "_id": 1,
                    "sender_id": 1,
                    "receiver_id": 1,
                    "message": 1,
                    "status": 1,
                    "created_at": 1,
                    "user_id": f"$user_info._id",
                    "username": "$user_info.username",
                    "full_name": {
                        "$concat": ["$user_info.first_name", " ", "$user_info.last_name"]
                    },
                    "avatar_url": "$user_info.profile.avatar_url",
                    "status_user": "$user_info.status",
                    "last_seen": "$user_info.last_seen"
                }
            },
            {"$sort": {"created_at": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ]
        
        return await self.aggregate(pipeline)
    
    async def get_pending_count(self, user_id: str) -> int:
        """Get count of pending friend requests for user"""
        if not ObjectId.is_valid(user_id):
            return 0
        
        return await self.count({
            "receiver_id": ObjectId(user_id),
            "status": FriendRequestStatus.PENDING
        })
    
    async def can_send_request(self, sender_id: str, receiver_id: str) -> bool:
        """Check if user can send friend request to another user"""
        result = await self.can_send_request_detailed(sender_id, receiver_id)
        return result["can_send"]
    
    async def can_send_request_detailed(self, sender_id: str, receiver_id: str) -> dict:
        """Check if user can send friend request to another user with detailed reason"""
        try:
            # Validate and convert ObjectIds
            if not ObjectId.is_valid(sender_id):
                return {"can_send": False, "reason": f"Invalid sender ID: {sender_id}"}
            if not ObjectId.is_valid(receiver_id):
                return {"can_send": False, "reason": f"Invalid receiver ID: {receiver_id}"}
            
            # Can't send request to yourself
            if sender_id == receiver_id:
                return {"can_send": False, "reason": "Cannot send friend request to yourself"}
            
            # Check if users are already friends
            from app.database.repositories.user_repository import UserRepository
            user_repo = UserRepository()
            
            are_friends = await user_repo.are_friends(sender_id, receiver_id)
            if are_friends:
                return {"can_send": False, "reason": "Users are already friends"}
            
            # Check if either user has blocked the other
            sender_blocked = await user_repo.is_blocked(sender_id, receiver_id)
            receiver_blocked = await user_repo.is_blocked(receiver_id, sender_id)
            
            if sender_blocked:
                return {"can_send": False, "reason": "You have blocked this user"}
            if receiver_blocked:
                return {"can_send": False, "reason": "This user has blocked you"}
            
            # Check if there's already a pending request
            existing_request = await self.get_existing_request(sender_id, receiver_id)
            if existing_request and existing_request.status == FriendRequestStatus.PENDING:
                if str(existing_request.sender_id) == sender_id:
                    return {"can_send": False, "reason": "You already sent a friend request to this user"}
                else:
                    return {"can_send": False, "reason": "This user already sent you a friend request"}
            
            return {"can_send": True, "reason": "OK"}
        except Exception as e:
            return {"can_send": False, "reason": f"Error validating friend request: {str(e)}"}
    
    async def cleanup_old_rejected_requests(self, days: int = 30) -> int:
        """Clean up old rejected friend requests"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.collection.delete_many({
            "status": FriendRequestStatus.REJECTED,
            "responded_at": {"$lt": cutoff_date}
        })
        
        return result.deleted_count
    
    async def get_request_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get friend request statistics for user"""
        if not ObjectId.is_valid(user_id):
            return {}
        
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"sender_id": ObjectId(user_id)},
                        {"receiver_id": ObjectId(user_id)}
                    ]
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_sent": {
                        "$sum": {"$cond": [{"$eq": ["$sender_id", ObjectId(user_id)]}, 1, 0]}
                    },
                    "total_received": {
                        "$sum": {"$cond": [{"$eq": ["$receiver_id", ObjectId(user_id)]}, 1, 0]}
                    },
                    "pending_sent": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$sender_id", ObjectId(user_id)]},
                                        {"$eq": ["$status", "pending"]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "pending_received": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$receiver_id", ObjectId(user_id)]},
                                        {"$eq": ["$status", "pending"]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "accepted_sent": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$sender_id", ObjectId(user_id)]},
                                        {"$eq": ["$status", "accepted"]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "accepted_received": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$receiver_id", ObjectId(user_id)]},
                                        {"$eq": ["$status", "accepted"]}
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