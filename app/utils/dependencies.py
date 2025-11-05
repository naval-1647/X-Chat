"""
FastAPI dependencies for ChatX API
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.auth import AuthUtils
from app.database.repositories import user_repo
from app.database.schemas import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = AuthUtils.verify_token(credentials.credentials, "access")
        if payload is None:
            raise credentials_exception
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (same as get_current_user but explicit)"""
    return current_user


async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    if credentials is None:
        return None
    
    try:
        # Verify token
        payload = AuthUtils.verify_token(credentials.credentials, "access")
        if payload is None:
            return None
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = await user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify admin privileges"""
    # For now, we'll check if user is the admin user created during setup
    # In a real system, you might have an is_admin field or role-based system
    from app.config import settings
    
    if current_user.username != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def verify_chat_access(chat_id: str, user_id: str) -> bool:
    """Verify if user has access to chat (to be used in route handlers)"""
    # This is a placeholder - actual implementation would check if user is participant
    # Will be implemented in chat routes
    return True


def verify_message_access(message_id: str, user_id: str) -> bool:
    """Verify if user has access to message (to be used in route handlers)"""
    # This is a placeholder - actual implementation would check if user can access the message
    # Will be implemented in message routes
    return True