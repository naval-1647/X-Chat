"""
User management routes for ChatX API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
import logging

from app.database.schemas.models import (
    UserProfileResponse,
    UserUpdateRequest,
    UserStatusUpdateRequest,
    PasswordChangeRequest,
    FriendRequestSendRequest,
    FriendRequestResponse,
    FriendRequestActionRequest,
    PaginatedResponse
)
from app.database.repositories import user_repo, friend_request_repo
from app.database.schemas import User, UserStatus
from app.utils.dependencies import get_current_user
from app.utils.auth import AuthUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/online/test")
async def test_online_endpoint():
    """Test endpoint to verify online route registration"""
    return {"status": "online endpoint is working", "message": "Route registered successfully"}

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return UserProfileResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        profile=current_user.profile.dict(),
        status=current_user.status,
        last_seen=current_user.last_seen,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    
    # Update user profile
    updated_user = await user_repo.update_profile(
        user_id=str(current_user.id),
        first_name=update_data.first_name,
        last_name=update_data.last_name,
        bio=update_data.bio,
        phone=update_data.phone,
        location=update_data.location
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return UserProfileResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        full_name=updated_user.full_name,
        profile=updated_user.profile.dict(),
        status=updated_user.status,
        last_seen=updated_user.last_seen,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.put("/status", status_code=status.HTTP_200_OK)
async def update_user_status(
    status_data: UserStatusUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user online status"""
    
    success = await user_repo.update_status(str(current_user.id), status_data.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update status"
        )
    
    return {"message": f"Status updated to {status_data.status.value}"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    
    # Verify current password
    if not AuthUtils.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_password_hash = AuthUtils.hash_password(password_data.new_password)
    
    # Update password
    updated_user = await user_repo.update_by_id(
        str(current_user.id),
        password_hash=new_password_hash
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
    
    return {"message": "Password changed successfully"}


@router.get("/search", response_model=PaginatedResponse)
async def search_users(
    q: str = Query(..., min_length=2, description="Search query for users"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
):
    """Search for users"""
    
    result = await user_repo.search_users(
        query=q,
        current_user_id=str(current_user.id),
        page=page,
        limit=limit
    )
    
    # Convert users to response format
    user_responses = []
    for user in result["items"]:
        user_responses.append(UserProfileResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            profile=user.profile.dict(),
            status=user.status,
            last_seen=user.last_seen,
            is_verified=user.is_verified,
            created_at=user.created_at
        ))
    
    return PaginatedResponse(
        items=user_responses,
        pagination=result["pagination"]
    )


@router.get("/online", response_model=List[UserProfileResponse])
async def get_online_users(
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Get currently online users"""
    print(f"🔍 get_online_users called with limit: {limit}, user: {current_user.username}")
    
    online_users = await user_repo.get_online_users(limit=limit)
    
    # Filter out blocked users and users who blocked current user
    filtered_users = []
    for user in online_users:
        if str(user.id) == str(current_user.id):
            continue
            
        # Check if either user blocked the other
        blocked_by_current = await user_repo.is_blocked(str(current_user.id), str(user.id))
        blocked_current = await user_repo.is_blocked(str(user.id), str(current_user.id))
        
        if not (blocked_by_current or blocked_current):
            filtered_users.append(UserProfileResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                profile=user.profile.dict(),
                status=user.status,
                last_seen=user.last_seen,
                is_verified=user.is_verified,
                created_at=user.created_at
            ))
    
    return filtered_users


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get user profile by ID"""
    
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if current user is blocked by the target user
    is_blocked = await user_repo.is_blocked(user_id, str(current_user.id))
    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return UserProfileResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        profile=user.profile.dict(),
        status=user.status,
        last_seen=user.last_seen,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@router.get("/friends/list", response_model=List[UserProfileResponse])
async def get_friends_list(current_user: User = Depends(get_current_user)):
    """Get user's friends list"""
    
    friends = await user_repo.get_friends(str(current_user.id))
    
    friend_responses = []
    for friend in friends:
        friend_responses.append(UserProfileResponse(
            id=str(friend.id),
            username=friend.username,
            email=friend.email,
            first_name=friend.first_name,
            last_name=friend.last_name,
            full_name=friend.full_name,
            profile=friend.profile.dict(),
            status=friend.status,
            last_seen=friend.last_seen,
            is_verified=friend.is_verified,
            created_at=friend.created_at
        ))
    
    return friend_responses


@router.post("/friends/request", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request_data: FriendRequestSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a friend request"""
    
    try:
        logger.info(f"🔍 send_friend_request called with user_id: {request_data.user_id}, current_user: {current_user.username}")
        
        # Get receiver by user ID
        receiver = await user_repo.get_by_id(request_data.user_id)
        if not receiver:
            logger.warning(f"❌ User not found: {request_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"✅ Found receiver: {receiver.username}")
        
        # Check if can send request
        sender_id = str(current_user.id)
        receiver_id = str(receiver.id)
        
        logger.info(f"🔍 Checking if can send request from {sender_id} to {receiver_id}")
        
        can_send_result = await friend_request_repo.can_send_request_detailed(
            sender_id,
            receiver_id
        )
        
        logger.info(f"🔍 Can send result: {can_send_result}")

        if not can_send_result["can_send"]:
            logger.warning(f"❌ Cannot send friend request: {can_send_result['reason']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot send friend request: {can_send_result['reason']}"
            )
        
        logger.info("✅ Can send friend request, creating...")
        
        # Create friend request
        friend_request = await friend_request_repo.create_friend_request(
            sender_id=str(current_user.id),
            receiver_id=str(receiver.id),
            message=request_data.message
        )
        
        if not friend_request:
            logger.error("❌ Failed to create friend request")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send friend request"
            )
        
        logger.info(f"✅ Friend request created: {friend_request.id}")
        
        # Create notification for receiver
        from app.database.repositories import notification_repo
        logger.info("🔍 Creating notification for receiver...")
        await notification_repo.create_friend_request_notification(
            recipient_id=str(receiver.id),
            sender_id=str(current_user.id),
            friend_request_id=str(friend_request.id),
            message=request_data.message
        )
        
        logger.info("✅ Notification created successfully")
        
        response = FriendRequestResponse(
            id=str(friend_request.id),
            sender_id=str(friend_request.sender_id),
            sender_username=current_user.username,
            sender_full_name=current_user.full_name,
            receiver_id=str(friend_request.receiver_id),
            receiver_username=receiver.username,
            receiver_full_name=receiver.full_name,
            status=friend_request.status,
            message=friend_request.message,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at
        )
        
        logger.info(f"✅ Friend request sent successfully: {response.id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in send_friend_request: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send friend request: {str(e)}"
        )


@router.get("/friends/requests/received", response_model=List[FriendRequestResponse])
async def get_received_friend_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get received friend requests"""
    
    try:
        requests_with_info = await friend_request_repo.get_requests_with_user_info(
            user_id=str(current_user.id),
            received=True,
            page=page,
            limit=limit
        )
        
        request_responses = []
        for req in requests_with_info:
            # Ensure we have valid data
            sender_username = req.get("username") or "Unknown User"
            sender_full_name = req.get("full_name") or sender_username
            
            request_responses.append(FriendRequestResponse(
                id=str(req["_id"]),
                sender_id=str(req["sender_id"]),
                sender_username=sender_username,
                sender_full_name=sender_full_name,
                receiver_id=str(req["receiver_id"]),
                receiver_username=current_user.username,
                receiver_full_name=current_user.full_name,
                status=str(req["status"]) if req["status"] else "pending",
                message=req.get("message"),
                created_at=req["created_at"],
                responded_at=None
            ))
        
        return request_responses
        
    except Exception as e:
        print(f"❌ Error in get_received_friend_requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get received friend requests: {str(e)}"
        )


@router.get("/friends/requests/sent", response_model=List[FriendRequestResponse])
async def get_sent_friend_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get sent friend requests"""
    
    try:
        requests_with_info = await friend_request_repo.get_requests_with_user_info(
            user_id=str(current_user.id),
            received=False,
            page=page,
            limit=limit
        )
        
        print(f"🔍 Debug - Found {len(requests_with_info)} sent friend requests")
        
        request_responses = []
        for i, req in enumerate(requests_with_info):
            print(f"🔍 Debug - Processing request {i+1}: username='{req.get('username')}', full_name='{req.get('full_name')}'")
            
            # Ensure we have valid data
            receiver_username = req.get("username") or "Unknown User"
            receiver_full_name = req.get("full_name") or receiver_username
            
            response_obj = FriendRequestResponse(
                id=str(req["_id"]),
                sender_id=str(req["sender_id"]),
                sender_username=current_user.username,
                sender_full_name=current_user.full_name,
                receiver_id=str(req["receiver_id"]),
                receiver_username=receiver_username,
                receiver_full_name=receiver_full_name,
                status=str(req["status"]) if req["status"] else "pending",
                message=req.get("message"),
                created_at=req["created_at"],
                responded_at=None
            )
            
            print(f"🔍 Debug - Created response: receiver_username='{response_obj.receiver_username}', receiver_full_name='{response_obj.receiver_full_name}'")
            request_responses.append(response_obj)
        
        print(f"🔍 Debug - Returning {len(request_responses)} friend request responses")
        print(f"🔍 DEBUG - FINAL JSON TO FRONTEND: {[r.dict() for r in request_responses]}")
        return request_responses
        
    except Exception as e:
        print(f"❌ Error in get_sent_friend_requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sent friend requests: {str(e)}"
        )


@router.post("/friends/requests/{request_id}/action", response_model=FriendRequestResponse)
async def handle_friend_request(
    request_id: str,
    action_data: FriendRequestActionRequest,
    current_user: User = Depends(get_current_user)
):
    """Accept or reject a friend request"""
    
    if action_data.action == "accept":
        friend_request = await friend_request_repo.accept_friend_request(
            request_id=request_id,
            user_id=str(current_user.id)
        )
    elif action_data.action == "reject":
        friend_request = await friend_request_repo.reject_friend_request(
            request_id=request_id,
            user_id=str(current_user.id)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'accept' or 'reject'"
        )
    
    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found or cannot be processed"
        )
    
    # Get sender info for response
    sender = await user_repo.get_by_id(str(friend_request.sender_id))
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sender information"
        )
    
    return FriendRequestResponse(
        id=str(friend_request.id),
        sender_id=str(friend_request.sender_id),
        sender_username=sender.username,
        sender_full_name=sender.full_name,
        receiver_id=str(friend_request.receiver_id),
        receiver_username=current_user.username,
        receiver_full_name=current_user.full_name,
        status=friend_request.status,
        message=friend_request.message,
        created_at=friend_request.created_at,
        responded_at=friend_request.responded_at
    )


@router.delete("/friends/requests/{request_id}", status_code=status.HTTP_200_OK)
async def cancel_friend_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a sent friend request"""
    
    success = await friend_request_repo.cancel_friend_request(
        request_id=request_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found or cannot be cancelled"
        )
    
    return {"message": "Friend request cancelled successfully"}


@router.delete("/friends/{friend_id}", status_code=status.HTTP_200_OK)  
async def remove_friend(
    friend_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a friend"""
    
    # Check if they are friends
    are_friends = await user_repo.are_friends(str(current_user.id), friend_id)
    if not are_friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in your friends list"
        )
    
    # Remove friend from both users' friend lists
    success1 = await user_repo.remove_friend(str(current_user.id), friend_id)
    success2 = await user_repo.remove_friend(friend_id, str(current_user.id))
    
    if not (success1 and success2):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove friend"
        )
    
    return {"message": "Friend removed successfully"}


@router.post("/block/{user_id}", status_code=status.HTTP_200_OK)
async def block_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Block a user"""
    
    # Check if user exists
    user_to_block = await user_repo.get_by_id(user_id)
    if not user_to_block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot block yourself
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )
    
    # Block user
    success = await user_repo.block_user(str(current_user.id), user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user"
        )
    
    return {"message": f"User {user_to_block.username} blocked successfully"}


@router.delete("/block/{user_id}", status_code=status.HTTP_200_OK)
async def unblock_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unblock a user"""
    
    # Check if user exists
    user_to_unblock = await user_repo.get_by_id(user_id)
    if not user_to_unblock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Unblock user
    success = await user_repo.unblock_user(str(current_user.id), user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock user"
        )
    
    return {"message": f"User {user_to_unblock.username} unblocked successfully"}


@router.get("/blocked/list", response_model=List[UserProfileResponse])
async def get_blocked_users(current_user: User = Depends(get_current_user)):
    """Get list of blocked users"""
    
    blocked_users = await user_repo.get_blocked_users(str(current_user.id))
    
    blocked_responses = []
    for user in blocked_users:
        blocked_responses.append(UserProfileResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            profile=user.profile.dict(),
            status=user.status,
            last_seen=user.last_seen,
            is_verified=user.is_verified,
            created_at=user.created_at
        ))
    
    return blocked_responses


@router.get("/online/test")
async def test_online_endpoint():
    """Test endpoint to verify route registration"""
    return {"status": "online endpoint is working", "message": "Route registered successfully"}

