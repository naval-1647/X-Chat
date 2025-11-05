"""
Chat system routes for ChatX API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.database.schemas.models import (
    ChatCreateRequest,
    ChatUpdateRequest,
    ChatResponse,
    ChatParticipantResponse,
    AddParticipantsRequest,
    UpdateParticipantRequest,
    PaginatedResponse
)
from app.database.repositories import chat_repo, user_repo
from app.database.schemas import User, ChatType
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/chats", tags=["Chat Management"])


@router.post("/test")
async def test_chat_endpoint():
    """Test endpoint to verify chat route registration"""
    return {"status": "chat endpoint is working", "message": "Route registered successfully"}

@router.post("/debug", status_code=status.HTTP_200_OK)
async def debug_chat_creation(request: dict):
    """Debug endpoint to see what data is being sent"""
    print(f"🔍 Debug chat creation - received data: {request}")
    return {"status": "debug", "received_data": request}

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: dict,  # Accept raw dict to handle different field names
    current_user: User = Depends(get_current_user)
):
    """Create a new chat (private or group)"""
    print(f"🔍 create_chat called with data: {chat_data}, user: {current_user.username}")
    
    try:
        # Handle different field name formats from frontend
        chat_type = chat_data.get('type') or chat_data.get('chat_type', 'direct')
        participant_ids = chat_data.get('participant_ids') or chat_data.get('participants', [])
        name = chat_data.get('name') or chat_data.get('title')
        description = chat_data.get('description')
        
        # Convert string to enum
        if chat_type == 'direct' or chat_type == 'private':
            chat_type_enum = ChatType.PRIVATE
        else:
            chat_type_enum = ChatType.GROUP
            
        print(f"🔍 Parsed: type={chat_type_enum}, participants={participant_ids}, name={name}")
        
        if chat_type_enum == ChatType.PRIVATE:
            # For private chat, must have exactly one other participant
            if len(participant_ids) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Private chat must have exactly one other participant"
                )
            
            other_user_id = participant_ids[0]
            
            # Validate other user exists
            other_user = await user_repo.get_by_id(other_user_id)
            if not other_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Participant user not found"
                )
            
            # Check if users are blocked
            current_blocked_other = await user_repo.is_blocked(str(current_user.id), other_user_id)
            other_blocked_current = await user_repo.is_blocked(other_user_id, str(current_user.id))
            
            if current_blocked_other or other_blocked_current:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create chat with blocked user"
                )
            
            # Create private chat
            chat = await chat_repo.create_private_chat(str(current_user.id), other_user_id)
            
        else:  # Group chat
            if not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Group chat must have a name"
                )
            
            if len(participant_ids) < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Group chat must have at least one other participant"
                )
            
            # Validate all participants exist
            for participant_id in participant_ids:
                participant = await user_repo.get_by_id(participant_id)
                if not participant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Participant {participant_id} not found"
                    )
            
            # Create group chat
            chat = await chat_repo.create_group_chat(
                creator_id=str(current_user.id),
                participant_ids=participant_ids,
                name=name,
                description=description
            )
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat"
            )
        
        # Get participant details for response
        participants_info = await chat_repo.get_chat_participants(str(chat.id))
        participants = []
        for p in participants_info:
            participants.append(ChatParticipantResponse(
                user_id=str(p["user_id"]),
                username=p["username"],
                full_name=p["full_name"],
                avatar_url=p.get("avatar_url"),
                joined_at=p["joined_at"],
                is_admin=p.get("is_admin", False),  # Default to False if missing
                is_muted=p.get("is_muted", False),  # Default to False if missing
                last_read_at=p.get("last_read_at")
            ))
        
        chat_response = ChatResponse(
            id=str(chat.id),
            type=chat.type,
            name=chat.name,
            description=chat.description,
            avatar_url=chat.avatar_url,
            participants=participants,
            created_by=str(chat.created_by),
            message_count=chat.message_count,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
            is_archived=chat.is_archived,
            is_pinned=chat.is_pinned
        )
        
        print(f"✅ Chat created successfully: {chat_response.id}, redirecting to chat")
        return chat_response
    except Exception as e:
        print(f"❌ Error creating chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to create chat: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def get_user_chats(
    chat_type: Optional[ChatType] = Query(None, description="Filter by chat type"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get user's chats"""
    
    result = await chat_repo.get_user_chats(
        user_id=str(current_user.id),
        chat_type=chat_type,
        page=page,
        limit=limit
    )
    
    # Convert chats to response format
    chat_responses = []
    for chat in result["items"]:
        # Get participant details
        participants_info = await chat_repo.get_chat_participants(str(chat.id))
        participants = []
        for p in participants_info:
            participants.append(ChatParticipantResponse(
                user_id=str(p["user_id"]),
                username=p["username"],
                full_name=p["full_name"],
                avatar_url=p.get("avatar_url"),
                joined_at=p["joined_at"],
                is_admin=p["is_admin"],
                is_muted=p["is_muted"],
                last_read_at=p.get("last_read_at")
            ))
        
        chat_responses.append(ChatResponse(
            id=str(chat.id),
            type=chat.type,
            name=chat.name,
            description=chat.description,
            avatar_url=chat.avatar_url,
            participants=participants,
            created_by=str(chat.created_by),
            message_count=chat.message_count,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
            is_archived=chat.is_archived,
            is_pinned=chat.is_pinned
        ))
    
    return PaginatedResponse(
        items=chat_responses,
        pagination=result["pagination"]
    )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat by ID"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    if not chat.is_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat"
        )
    
    # Get participant details
    participants_info = await chat_repo.get_chat_participants(chat_id)
    participants = []
    for p in participants_info:
        participants.append(ChatParticipantResponse(
            user_id=str(p["user_id"]),
            username=p["username"],
            full_name=p["full_name"],
            avatar_url=p.get("avatar_url"),
            joined_at=p["joined_at"],
            is_admin=p["is_admin"],
            is_muted=p["is_muted"],
            last_read_at=p.get("last_read_at")
        ))
    
    return ChatResponse(
        id=str(chat.id),
        type=chat.type,
        name=chat.name,
        description=chat.description,
        avatar_url=chat.avatar_url,
        participants=participants,
        created_by=str(chat.created_by),
        message_count=chat.message_count,
        last_message_at=chat.last_message_at,
        created_at=chat.created_at,
        is_archived=chat.is_archived,
        is_pinned=chat.is_pinned
    )


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    update_data: ChatUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update chat information (group chats only, admin required)"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Only group chats can be updated
    if chat.type != ChatType.GROUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only group chats can be updated"
        )
    
    # Check if user is admin
    if not chat.is_admin(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Update chat
    updated_chat = await chat_repo.update_chat_info(
        chat_id=chat_id,
        user_id=str(current_user.id),
        name=update_data.name,
        description=update_data.description
    )
    
    if not updated_chat:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat"
        )
    
    # Get updated participant details
    participants_info = await chat_repo.get_chat_participants(chat_id)
    participants = []
    for p in participants_info:
        participants.append(ChatParticipantResponse(
            user_id=str(p["user_id"]),
            username=p["username"],
            full_name=p["full_name"],
            avatar_url=p.get("avatar_url"),
            joined_at=p["joined_at"],
            is_admin=p["is_admin"],
            is_muted=p["is_muted"],
            last_read_at=p.get("last_read_at")
        ))
    
    return ChatResponse(
        id=str(updated_chat.id),
        type=updated_chat.type,
        name=updated_chat.name,
        description=updated_chat.description,
        avatar_url=updated_chat.avatar_url,
        participants=participants,
        created_by=str(updated_chat.created_by),
        message_count=updated_chat.message_count,
        last_message_at=updated_chat.last_message_at,
        created_at=updated_chat.created_at,
        is_archived=updated_chat.is_archived,
        is_pinned=updated_chat.is_pinned
    )


@router.post("/{chat_id}/participants", status_code=status.HTTP_200_OK)
async def add_participants(
    chat_id: str,
    participants_data: AddParticipantsRequest,
    current_user: User = Depends(get_current_user)
):
    """Add participants to group chat (admin required)"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Only group chats can have participants added
    if chat.type != ChatType.GROUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only add participants to group chats"
        )
    
    # Check if user is admin
    if not chat.is_admin(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Add each participant
    added_count = 0
    for user_id in participants_data.user_ids:
        # Validate user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            continue
        
        # Add participant
        success = await chat_repo.add_participant(chat_id, user_id, str(current_user.id))
        if success:
            added_count += 1
            
            # Create notification for added user
            from app.database.repositories import notification_repo
            await notification_repo.create_chat_invite_notification(
                invited_user_id=user_id,
                inviter_id=str(current_user.id),
                chat_id=chat_id,
                chat_name=chat.name or "Group Chat"
            )
    
    return {"message": f"Added {added_count} participants to chat"}


@router.delete("/{chat_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def remove_participant(
    chat_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove participant from group chat (admin required or self-removal)"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Only group chats can have participants removed
    if chat.type != ChatType.GROUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only remove participants from group chats"
        )
    
    # Check permissions (admin can remove anyone, users can remove themselves)
    if not (chat.is_admin(current_user.id) or user_id == str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Remove participant
    success = await chat_repo.remove_participant(chat_id, user_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove participant"
        )
    
    return {"message": "Participant removed from chat"}


@router.put("/{chat_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def update_participant(
    chat_id: str,
    user_id: str,
    update_data: UpdateParticipantRequest,
    current_user: User = Depends(get_current_user)
):
    """Update participant role/settings (admin required)"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is admin
    if not chat.is_admin(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Update admin role if specified
    if update_data.is_admin is not None:
        success = await chat_repo.update_participant_role(
            chat_id=chat_id,
            user_id=user_id,
            is_admin=update_data.is_admin,
            updated_by=str(current_user.id)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update participant role"
            )
    
    # Update mute status if specified
    if update_data.is_muted is not None:
        if update_data.is_muted:
            success = await chat_repo.mute_participant(chat_id, user_id, str(current_user.id))
        else:
            success = await chat_repo.unmute_participant(chat_id, user_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update participant mute status"
            )
    
    return {"message": "Participant updated successfully"}


@router.post("/{chat_id}/archive", status_code=status.HTTP_200_OK)
async def archive_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archive chat"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    if not chat.is_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat"
        )
    
    success = await chat_repo.archive_chat(chat_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive chat"
        )
    
    return {"message": "Chat archived successfully"}


@router.delete("/{chat_id}/archive", status_code=status.HTTP_200_OK)
async def unarchive_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unarchive chat"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    if not chat.is_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat"
        )
    
    success = await chat_repo.unarchive_chat(chat_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unarchive chat"
        )
    
    return {"message": "Chat unarchived successfully"}


@router.post("/{chat_id}/pin", status_code=status.HTTP_200_OK)
async def pin_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Pin chat"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    if not chat.is_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat"
        )
    
    success = await chat_repo.pin_chat(chat_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pin chat"
        )
    
    return {"message": "Chat pinned successfully"}


@router.delete("/{chat_id}/pin", status_code=status.HTTP_200_OK)
async def unpin_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unpin chat"""
    
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    if not chat.is_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat"
        )
    
    success = await chat_repo.unpin_chat(chat_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unpin chat"
        )
    
    return {"message": "Chat unpinned successfully"}


@router.get("/search", response_model=PaginatedResponse)
async def search_chats(
    query: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Search user's chats"""
    
    result = await chat_repo.search_chats(
        user_id=str(current_user.id),
        query=query,
        page=page,
        limit=limit
    )
    
    # Convert chats to response format
    chat_responses = []
    for chat in result["items"]:
        # Get participant details
        participants_info = await chat_repo.get_chat_participants(str(chat.id))
        participants = []
        for p in participants_info:
            participants.append(ChatParticipantResponse(
                user_id=str(p["user_id"]),
                username=p["username"],
                full_name=p["full_name"],
                avatar_url=p.get("avatar_url"),
                joined_at=p["joined_at"],
                is_admin=p["is_admin"],
                is_muted=p["is_muted"],
                last_read_at=p.get("last_read_at")
            ))
        
        chat_responses.append(ChatResponse(
            id=str(chat.id),
            type=chat.type,
            name=chat.name,
            description=chat.description,
            avatar_url=chat.avatar_url,
            participants=participants,
            created_by=str(chat.created_by),
            message_count=chat.message_count,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
            is_archived=chat.is_archived,
            is_pinned=chat.is_pinned
        ))
    
    return PaginatedResponse(
        items=chat_responses,
        pagination=result["pagination"]
    )