"""
Authentication utilities for ChatX API
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import bcrypt
from jose import JWTError, jwt

from app.config import security_settings


class AuthUtils:
    """Authentication utility functions"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with SHA-256 preprocessing for long passwords"""
        if not isinstance(password, str):
            password = str(password)
        
        # For very long passwords, use SHA-256 preprocessing
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Use SHA-256 to reduce long passwords to a fixed size
            password = hashlib.sha256(password_bytes).hexdigest()
        
        # Hash using bcrypt directly
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if not isinstance(plain_password, str):
            plain_password = str(plain_password)
        
        # Apply same SHA-256 preprocessing as in hash_password for consistency
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = hashlib.sha256(password_bytes).hexdigest()
        
        # Verify using bcrypt directly
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=security_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=security_settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                security_settings.JWT_SECRET_KEY,
                algorithms=[security_settings.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                return None
            
            return payload
            
        except JWTError:
            return None
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        payload = AuthUtils.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
    
    @staticmethod
    def create_token_pair(user_id: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Create both access and refresh tokens"""
        token_data = {"sub": user_id}
        if additional_data:
            token_data.update(additional_data)
        
        access_token = AuthUtils.create_access_token(token_data)
        refresh_token = AuthUtils.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": security_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """Create new access token from refresh token"""
        payload = AuthUtils.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Create new access token
        access_token = AuthUtils.create_access_token({"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": security_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }


# Utility functions for FastAPI dependencies
def get_password_hash(password: str) -> str:
    """Get password hash"""
    return AuthUtils.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return AuthUtils.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token"""
    return AuthUtils.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token"""
    return AuthUtils.create_refresh_token(data)