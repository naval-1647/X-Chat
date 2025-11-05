"""
Message management routes for ChatX API
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.database.schemas.models import (
    MessageResponse,
    MessageSendRequest,
    MessageUpdateRequest,
    PaginatedResponse,
    PaginationInfo
)
from app.database.repositories import message_repo, chat_repo, user_repo
from app.database.schemas import User, Message, MessageType, MessageStatus
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["Message Management"])


@router.get("/{chat_id}", response_model=PaginatedResponse)
async def get_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a chat"""
    print(f"🔍 get_messages called - chat_id: {chat_id}, page: {page}, limit: {limit}, user: {current_user.username}")
    
    # Verify user is participant of this chat
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    is_participant = await chat_repo.is_participant(chat_id, str(current_user.id))
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Get messages
    messages_result = await message_repo.get_chat_messages(
        chat_id=chat_id,
        page=page,
        limit=limit
    )
    
    messages = messages_result.get("items", [])
    total = messages_result.get("pagination", {}).get("total", 0)
    
    # Convert to response format
    message_responses = []
    for msg in messages:
        # Get sender info
        sender = await user_repo.get_by_id(str(msg.sender_id))
        
        # Convert media to response format
        media_response = None
        if msg.media:
            from app.database.schemas.models import MessageMediaResponse
            media_response = MessageMediaResponse(
                file_url=msg.media.file_url,
                file_name=msg.media.file_name,
                file_size=msg.media.file_size,
                mime_type=msg.media.mime_type,
                thumbnail_url=msg.media.thumbnail_url,
                duration=msg.media.duration,
                dimensions=msg.media.dimensions
            )
        
        message_responses.append(MessageResponse(
            id=str(msg.id),
            content=msg.content,
            message_type=msg.message_type.value,
            media=media_response,
            chat_id=str(msg.chat_id),
            sender_id=str(msg.sender_id),
            sender_username=sender.username if sender else "Unknown",
            sender_full_name=sender.full_name if sender else "Unknown User",
            sender_avatar_url=sender.profile.avatar_url if sender and sender.profile else None,
            reply_to_message_id=str(msg.reply_to_message_id) if msg.reply_to_message_id else None,
            status=msg.status.value,
            is_edited=msg.is_edited,
            edited_at=msg.edited_at,
            created_at=msg.created_at,
            updated_at=msg.updated_at
        ))
    
    # Create pagination info
    total_pages = (total + limit - 1) // limit
    pagination_info = PaginationInfo(
        page=page,
        limit=limit,
        total=total,
        pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return PaginatedResponse(
        items=message_responses,
        pagination=pagination_info
    )


@router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a message to a chat"""
    print(f"🔍 send_message called - data: {message_data}, user: {current_user.username}")
    
    # Verify chat exists and user is participant
    chat = await chat_repo.get_by_id(message_data.chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    is_participant = await chat_repo.is_participant(message_data.chat_id, str(current_user.id))
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Create message
    message = await message_repo.create_message(
        content=message_data.content,
        chat_id=message_data.chat_id,
        sender_id=str(current_user.id),
        message_type=MessageType(message_data.message_type) if message_data.message_type else MessageType.TEXT,
        reply_to_message_id=message_data.reply_to_message_id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )
    
    # Update chat's last message info
    await chat_repo.update_last_message(message_data.chat_id, str(message.id))
    
    # Convert media to response format
    media_response = None
    if message.media:
        from app.database.schemas.models import MessageMediaResponse
        media_response = MessageMediaResponse(
            file_url=message.media.file_url,
            file_name=message.media.file_name,
            file_size=message.media.file_size,
            mime_type=message.media.mime_type,
            thumbnail_url=message.media.thumbnail_url,
            duration=message.media.duration,
            dimensions=message.media.dimensions
        )
    
    return MessageResponse(
        id=str(message.id),
        content=message.content,
        message_type=message.message_type.value,
        media=media_response,
        chat_id=str(message.chat_id),
        sender_id=str(message.sender_id),
        sender_username=current_user.username,
        sender_full_name=current_user.full_name,
        sender_avatar_url=current_user.profile.avatar_url if current_user.profile else None,
        reply_to_message_id=str(message.reply_to_message_id) if message.reply_to_message_id else None,
        status=message.status.value,
        is_edited=message.is_edited,
        edited_at=message.edited_at,
        created_at=message.created_at,
        updated_at=message.updated_at
    )


@router.put("/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: str,
    update_data: MessageUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Edit a message"""
    
    # Get message
    message = await message_repo.get_by_id(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if user is the sender
    if str(message.sender_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )
    
    # Update message
    updated_message = await message_repo.update_message_content(
        message_id=message_id,
        new_content=update_data.content,
        user_id=str(current_user.id)
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )
    
    # Convert media to response format
    media_response = None
    if updated_message.media:
        from app.database.schemas.models import MessageMediaResponse
        media_response = MessageMediaResponse(
            file_url=updated_message.media.file_url,
            file_name=updated_message.media.file_name,
            file_size=updated_message.media.file_size,
            mime_type=updated_message.media.mime_type,
            thumbnail_url=updated_message.media.thumbnail_url,
            duration=updated_message.media.duration,
            dimensions=updated_message.media.dimensions
        )
    
    return MessageResponse(
        id=str(updated_message.id),
        content=updated_message.content,
        message_type=updated_message.message_type.value,
        media=media_response,
        chat_id=str(updated_message.chat_id),
        sender_id=str(updated_message.sender_id),
        sender_username=current_user.username,
        sender_full_name=current_user.full_name,
        sender_avatar_url=current_user.profile.avatar_url if current_user.profile else None,
        reply_to_message_id=str(updated_message.reply_to_message_id) if updated_message.reply_to_message_id else None,
        status=updated_message.status.value,
        is_edited=updated_message.is_edited,
        edited_at=updated_message.edited_at,
        created_at=updated_message.created_at,
        updated_at=updated_message.updated_at
    )


@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a message"""
    
    # Get message
    message = await message_repo.get_by_id(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if user is the sender
    if str(message.sender_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )
    
    # Delete message
    success = await message_repo.delete_message(message_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )
    
    return {"message": "Message deleted successfully"}


@router.post("/{chat_id}/read", status_code=status.HTTP_200_OK)
async def mark_messages_as_read(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark all messages in a chat as read for current user"""
    
    # Verify chat exists and user is participant
    chat = await chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is participant
    is_participant = await chat_repo.is_participant(chat_id, str(current_user.id))
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Mark messages as read - mark all unread messages in the chat
    unread_messages = await message_repo.get_unread_messages(chat_id, str(current_user.id))
    success = True
    for msg in unread_messages:
        msg_success = await message_repo.mark_as_seen(str(msg.id), str(current_user.id))
        if not msg_success:
            success = False
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read"
        )
    
    return {"message": "Messages marked as read"}


@router.post("/upload/{chat_id}")
async def upload_media_message(
    chat_id: str,
    file: UploadFile = File(...),
    message_type: str = Form(...),
    content: Optional[str] = Form(None),
    reply_to_message_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    📸 Upload photo, video, or document and send as message
    
    Supported file types:
    - Images: jpeg, jpg, png, gif, webp
    - Videos: mp4, avi, mov, wmv, flv  
    - Audio: mp3, wav, ogg, m4a
    - Documents: pdf, doc, docx, txt, rtf
    """
    print(f"🔍 upload_media_message called - chat_id: {chat_id}, file: {file.filename}, type: {message_type}, user: {current_user.username}")
    
    # Validate chat exists and user is participant
    is_participant = await chat_repo.is_participant(chat_id, str(current_user.id))
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Validate message type
    valid_media_types = ["image", "video", "audio", "document"]
    if message_type not in valid_media_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message type. Must be one of: {valid_media_types}"
        )
    
    # Validate file type based on message type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    allowed_extensions = {
        "image": ["jpeg", "jpg", "png", "gif", "webp"],
        "video": ["mp4", "avi", "mov", "wmv", "flv"],
        "audio": ["mp3", "wav", "ogg", "m4a"],
        "document": ["pdf", "doc", "docx", "txt", "rtf"]
    }
    
    if file_extension not in allowed_extensions.get(message_type, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for {message_type}. Allowed: {allowed_extensions[message_type]}"
        )
    
    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large. Maximum 10MB allowed."
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create file URL (you might want to use a proper CDN URL in production)
    file_url = f"/api/v1/messages/files/{safe_filename}"
    
    # Create media message
    try:
        from app.database.schemas import MessageMedia
        
        media_data = MessageMedia(
            file_url=file_url,
            file_name=file.filename,
            file_size=len(file_content),
            mime_type=file.content_type or "application/octet-stream"
        )
        
        message = await message_repo.create_message(
            content=content or f"Shared a {message_type}",
            chat_id=chat_id,
            sender_id=str(current_user.id),
            message_type=MessageType(message_type.lower()),
            reply_to_message_id=reply_to_message_id,
            media=media_data
        )
        
        # Update chat's last message
        await chat_repo.update_last_message(chat_id, str(message.id))
        
        # Get sender info for response
        sender = await user_repo.get_by_id(str(current_user.id))
        
        # Convert media to response format
        media_response = None
        if message.media:
            from app.database.schemas.models import MessageMediaResponse
            media_response = MessageMediaResponse(
                file_url=message.media.file_url,
                file_name=message.media.file_name,
                file_size=message.media.file_size,
                mime_type=message.media.mime_type,
                thumbnail_url=message.media.thumbnail_url,
                duration=message.media.duration,
                dimensions=message.media.dimensions
            )
        
        response = MessageResponse(
            id=str(message.id),
            chat_id=str(message.chat_id),
            sender_id=str(message.sender_id),
            sender_username=sender.username if sender else "Unknown",
            sender_full_name=sender.full_name if sender else "Unknown User",
            sender_avatar_url=sender.profile.avatar_url if sender and sender.profile else None,
            content=message.content,
            message_type=message.message_type.value,
            media=media_response,
            reply_to_message_id=str(message.reply_to_message_id) if message.reply_to_message_id else None,
            status=message.status.value,
            is_edited=message.is_edited,
            edited_at=message.edited_at,
            created_at=message.created_at,
            updated_at=message.updated_at
        )
        
        return response
        
    except Exception as e:
        # Clean up file if message creation failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create media message: {str(e)}"
        )


@router.get("/files/{filename}")
async def get_uploaded_file(filename: str):
    """
    📁 Serve uploaded media files
    """
    file_path = os.path.join("uploads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path)