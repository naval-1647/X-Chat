"""
Configuration settings for ChatX API
"""
import os
from typing import List, Optional
from pydantic import BaseModel, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    app_name: str = os.getenv("APP_NAME", "ChatX API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8005"))
    
    # Database Configuration - MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "chatx_db")
    mongodb_username: Optional[str] = os.getenv("MONGODB_USERNAME")
    mongodb_password: Optional[str] = os.getenv("MONGODB_PASSWORD")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_uri: str = os.getenv("REDIS_URI", "redis://localhost:6379")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "300"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Password Hashing
    password_hash_algorithm: str = os.getenv("PASSWORD_HASH_ALGORITHM", "bcrypt")
    bcrypt_rounds: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    # File Upload Configuration
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads/")
    allowed_image_types: List[str] = os.getenv("ALLOWED_IMAGE_TYPES", "jpeg,jpg,png,gif,webp").split(",")
    allowed_video_types: List[str] = os.getenv("ALLOWED_VIDEO_TYPES", "mp4,avi,mov,wmv,flv").split(",")
    allowed_audio_types: List[str] = os.getenv("ALLOWED_AUDIO_TYPES", "mp3,wav,ogg,m4a").split(",")
    allowed_document_types: List[str] = os.getenv("ALLOWED_DOCUMENT_TYPES", "pdf,doc,docx,txt,rtf").split(",")
    
    # Email Configuration
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@chatx.com")
    
    # Security Settings
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Admin Configuration
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@chatx.com")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change-this-admin-password")
    
    # Notification Settings
    enable_push_notifications: bool = os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true"
    fcm_server_key: Optional[str] = os.getenv("FCM_SERVER_KEY")
    
    # WebSocket Settings
    ws_heartbeat_interval: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    ws_max_connections_per_user: int = int(os.getenv("WS_MAX_CONNECTIONS_PER_USER", "5"))
    
    # Background Tasks
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    
    @property
    def mongodb_url(self) -> str:
        """Get complete MongoDB connection URL"""
        if self.mongodb_username and self.mongodb_password:
            return f"mongodb://{self.mongodb_username}:{self.mongodb_password}@{self.mongodb_uri.replace('mongodb://', '')}"
        return self.mongodb_uri
    
    @property
    def redis_url(self) -> str:
        """Get complete Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"




# Global settings instance



# Global settings instance
settings = Settings()


# Database settings
class DatabaseSettings:
    """Database-specific settings"""
    MONGODB_URI = settings.mongodb_url
    DATABASE_NAME = settings.mongodb_database
    
    # Collection names
    USERS_COLLECTION = "users"
    CHATS_COLLECTION = "chats"
    MESSAGES_COLLECTION = "messages"
    NOTIFICATIONS_COLLECTION = "notifications"
    FRIEND_REQUESTS_COLLECTION = "friend_requests"
    BLOCKED_USERS_COLLECTION = "blocked_users"


# Redis settings
class RedisSettings:
    """Redis-specific settings"""
    REDIS_URI = settings.redis_url
    
    # Redis key prefixes
    USER_PRESENCE_PREFIX = "presence:user:"
    CHAT_TYPING_PREFIX = "typing:chat:"
    USER_SESSIONS_PREFIX = "sessions:user:"
    CHAT_SUBSCRIBERS_PREFIX = "subscribers:chat:"
    
    # Channel names for pub/sub
    MESSAGE_CHANNEL = "chat:messages"
    PRESENCE_CHANNEL = "user:presence"
    TYPING_CHANNEL = "chat:typing"
    NOTIFICATION_CHANNEL = "user:notifications"


# Security settings
class SecuritySettings:
    """Security-specific settings"""
    JWT_SECRET_KEY = settings.jwt_secret_key
    JWT_ALGORITHM = settings.jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes
    REFRESH_TOKEN_EXPIRE_DAYS = settings.jwt_refresh_token_expire_days
    
    BCRYPT_ROUNDS = settings.bcrypt_rounds
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute


# File upload settings
class UploadSettings:
    """File upload specific settings"""
    MAX_FILE_SIZE = settings.max_file_size
    UPLOAD_DIR = settings.upload_dir
    
    ALLOWED_IMAGE_TYPES = settings.allowed_image_types
    ALLOWED_VIDEO_TYPES = settings.allowed_video_types
    ALLOWED_AUDIO_TYPES = settings.allowed_audio_types
    ALLOWED_DOCUMENT_TYPES = settings.allowed_document_types
    
    @staticmethod
    def get_all_allowed_types() -> List[str]:
        """Get all allowed file types"""
        return (
            UploadSettings.ALLOWED_IMAGE_TYPES +
            UploadSettings.ALLOWED_VIDEO_TYPES +
            UploadSettings.ALLOWED_AUDIO_TYPES +
            UploadSettings.ALLOWED_DOCUMENT_TYPES
        )


# Export commonly used settings
db_settings = DatabaseSettings()
redis_settings = RedisSettings()
security_settings = SecuritySettings()
upload_settings = UploadSettings()