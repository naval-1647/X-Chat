"""
Authentication routes for ChatX API
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.database.schemas.models import (
    UserRegisterRequest,
    UserLoginRequest, 
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse
)
from app.database.repositories import user_repo
from app.utils.auth import AuthUtils
from app.utils.dependencies import get_current_user, security
from app.database.schemas import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterRequest):
    """Register a new user"""
    
    # Check if username already exists
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = AuthUtils.hash_password(user_data.password)
    
    # Create user
    try:
        user = await user_repo.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone
        )
        
        # Return user profile data
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLoginRequest):
    """Login user and return JWT tokens"""
    
    # Get user by username or email
    user = await user_repo.get_by_username_or_email(login_data.username_or_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
    
    # Verify password
    if not AuthUtils.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update user status to online
    await user_repo.update_status(str(user.id), user.status)
    
    # Create token pair
    token_data = AuthUtils.create_token_pair(
        user_id=str(user.id),
        additional_data={
            "username": user.username,
            "email": user.email
        }
    )
    
    return TokenResponse(**token_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    
    # Verify refresh token and get new access token
    token_data = AuthUtils.refresh_access_token(refresh_data.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return TokenResponse(**token_data)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user (update status to offline)"""
    
    # Update user status to offline
    await user_repo.update_last_seen(str(current_user.id))
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    
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


@router.post("/verify-token", status_code=status.HTTP_200_OK)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    
    # Verify token
    payload = AuthUtils.verify_token(credentials.credentials, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Check if user exists and is active
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "valid": True,
        "user_id": user_id,
        "username": user.username,
        "expires_at": payload.get("exp")
    }