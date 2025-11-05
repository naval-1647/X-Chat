"""
Database initialization and connection management for ChatX API
"""
import asyncio
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.config import settings
from app.database.schemas import (
    User, Chat, Message, FriendRequest, 
    Notification, BlockedUser
)

# Setup logging
logger = logging.getLogger(__name__)

# Global database instances
mongodb_client: Optional[AsyncIOMotorClient] = None
redis_client: Optional[Redis] = None
redis_async_client: Optional[AsyncRedis] = None


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.redis_client: Optional[Redis] = None
        self.redis_async_client: Optional[AsyncRedis] = None
    
    async def connect_mongodb(self):
        """Initialize MongoDB connection and Beanie ODM"""
        try:
            logger.info(f"=== MongoDB Connection Details ===")
            logger.info(f"URI: {settings.mongodb_uri}")
            logger.info(f"Database: {settings.mongodb_database}")
            logger.info("Creating MongoDB client...")
            
            # Create MongoDB client
            self.mongodb_client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=10000,
                connectTimeoutMS=10000,
            )
            logger.info("MongoDB client created successfully")
            
            # Test connection
            logger.info("Testing MongoDB connection...")
            await self.mongodb_client.admin.command('ismaster')
            logger.info("MongoDB connection test successful")
            
            # Initialize Beanie with document models
            logger.info("Initializing Beanie ODM...")
            await init_beanie(
                database=self.mongodb_client[settings.mongodb_database],
                document_models=[
                    User,
                    Chat,
                    Message,
                    FriendRequest,
                    Notification,
                    BlockedUser,
                ],
                allow_index_dropping=True  # Allow dropping and recreating indexes
            )
            logger.info("Beanie ODM initialized with all document models")
            
            # Create indexes
            logger.info("Creating database indexes...")
            await self.create_indexes()
            logger.info("Database indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"=== MONGODB CONNECTION FAILED ===")
            logger.error(f"Error: {e}")
            logger.error(f"URI attempted: {settings.mongodb_uri}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def connect_redis(self):
        """Initialize Redis connections"""
        try:
            logger.info("Connecting to Redis...")
            
            # Synchronous Redis client for simple operations
            self.redis_client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test sync connection
            self.redis_client.ping()
            logger.info("Redis sync client connected successfully")
            
            # Asynchronous Redis client for pub/sub
            self.redis_async_client = AsyncRedis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test async connection
            await self.redis_async_client.ping()
            logger.info("Redis async client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect_mongodb(self):
        """Close MongoDB connection"""
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info("MongoDB connection closed")
    
    async def disconnect_redis(self):
        """Close Redis connections"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis sync client closed")
        
        if self.redis_async_client:
            await self.redis_async_client.close()
            logger.info("Redis async client closed")
    
    async def create_indexes(self):
        """Create additional database indexes"""
        try:
            logger.info("Creating database indexes...")
            
            # MongoDB database
            db = self.mongodb_client[settings.mongodb_database]
            
            # Additional indexes for better performance
            await db.users.create_index([
                ("username", 1),
                ("email", 1),
                ("status", 1),
                ("is_active", 1),
                ("created_at", -1)
            ])
            
            await db.chats.create_index([
                ("participants.user_id", 1),
                ("type", 1),
                ("last_message_at", -1),
                ("created_at", -1)
            ])
            
            await db.messages.create_index([
                ("chat_id", 1),
                ("created_at", -1),
                ("sender_id", 1),
                ("message_type", 1)
            ])
            
            await db.notifications.create_index([
                ("user_id", 1),
                ("is_read", 1),
                ("created_at", -1),
                ("type", 1)
            ])
            
            await db.friend_requests.create_index([
                ("sender_id", 1),
                ("receiver_id", 1),
                ("status", 1),
                ("created_at", -1)
            ])
            
            await db.blocked_users.create_index([
                ("blocker_id", 1),
                ("blocked_id", 1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # Don't raise here as it's not critical for app startup


# Global database manager instance
db_manager = DatabaseManager()


async def init_database():
    """Initialize all database connections"""
    logger.info("=== Starting database initialization ===")
    
    try:
        logger.info("Step 1: Connecting to MongoDB...")
        # Connect to MongoDB
        await db_manager.connect_mongodb()
        logger.info("Step 1: MongoDB connection successful!")
        
        logger.info("Step 2: Connecting to Redis...")
        # Connect to Redis (optional)
        try:
            await db_manager.connect_redis()
            logger.info("Step 2: Redis connection successful!")
            redis_connected = True
        except Exception as redis_error:
            logger.warning(f"Redis connection failed: {redis_error}")
            logger.warning("Continuing without Redis - some features may be limited")
            redis_connected = False
        
        # Set global instances
        global mongodb_client, redis_client, redis_async_client
        mongodb_client = db_manager.mongodb_client
        if redis_connected:
            redis_client = db_manager.redis_client
            redis_async_client = db_manager.redis_async_client
        else:
            redis_client = None
            redis_async_client = None
        
        logger.info("=== DATABASE INITIALIZATION SUCCESSFUL ===")
        logger.info("✅ MongoDB: Connected and initialized")
        if redis_connected:
            logger.info("✅ Redis: Connected")
        else:
            logger.info("⚠️ Redis: Not available (optional)")
        logger.info("✅ All collections and indexes created")
        logger.info("✅ System ready for user registration and messaging")
        
    except Exception as e:
        logger.error(f"=== DATABASE INITIALIZATION FAILED ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def close_database():
    """Close all database connections"""
    logger.info("Closing database connections...")
    
    try:
        await db_manager.disconnect_mongodb()
        await db_manager.disconnect_redis()
        logger.info("All database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance"""
    global mongodb_client
    if mongodb_client is None:
        raise RuntimeError("MongoDB client not initialized")
    return mongodb_client


def get_redis_client() -> Redis:
    """Get Redis sync client instance"""
    global redis_client
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


def get_redis_async_client() -> AsyncRedis:
    """Get Redis async client instance"""
    global redis_async_client
    if redis_async_client is None:
        raise RuntimeError("Redis async client not initialized")
    return redis_async_client


class RedisManager:
    """Redis operations manager"""
    
    @staticmethod
    def get_user_presence_key(user_id: str) -> str:
        """Get Redis key for user presence"""
        return f"user:presence:{user_id}"
    
    @staticmethod
    def get_chat_typing_key(chat_id: str) -> str:
        """Get Redis key for chat typing indicators"""
        return f"chat:typing:{chat_id}"
    
    @staticmethod
    def get_user_sessions_key(user_id: str) -> str:
        """Get Redis key for user WebSocket sessions"""
        return f"user:sessions:{user_id}"
    
    @staticmethod
    def get_chat_subscribers_key(chat_id: str) -> str:
        """Get Redis key for chat subscribers"""
        return f"chat:subscribers:{chat_id}"
    
    @staticmethod
    async def set_user_presence(user_id: str, status: str, expire_seconds: int = 3600):
        """Set user presence in Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_presence_key(user_id)
        await redis.setex(key, expire_seconds, status)
    
    @staticmethod
    async def get_user_presence(user_id: str) -> Optional[str]:
        """Get user presence from Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_presence_key(user_id)
        return await redis.get(key)
    
    @staticmethod
    async def remove_user_presence(user_id: str):
        """Remove user presence from Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_presence_key(user_id)
        await redis.delete(key)
    
    @staticmethod
    async def add_user_session(user_id: str, session_id: str):
        """Add user WebSocket session to Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_sessions_key(user_id)
        await redis.sadd(key, session_id)
        await redis.expire(key, 7200)  # 2 hours
    
    @staticmethod
    async def remove_user_session(user_id: str, session_id: str):
        """Remove user WebSocket session from Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_sessions_key(user_id)
        await redis.srem(key, session_id)
    
    @staticmethod
    async def get_user_sessions(user_id: str) -> set:
        """Get all user WebSocket sessions from Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_user_sessions_key(user_id)
        return await redis.smembers(key)
    
    @staticmethod
    async def subscribe_to_chat(chat_id: str, user_id: str):
        """Subscribe user to chat notifications"""
        redis = get_redis_async_client()
        key = RedisManager.get_chat_subscribers_key(chat_id)
        await redis.sadd(key, user_id)
    
    @staticmethod
    async def unsubscribe_from_chat(chat_id: str, user_id: str):
        """Unsubscribe user from chat notifications"""
        redis = get_redis_async_client()
        key = RedisManager.get_chat_subscribers_key(chat_id)
        await redis.srem(key, user_id)
    
    @staticmethod
    async def get_chat_subscribers(chat_id: str) -> set:
        """Get all chat subscribers from Redis"""
        redis = get_redis_async_client()
        key = RedisManager.get_chat_subscribers_key(chat_id)
        return await redis.smembers(key)


# Redis manager instance
redis_manager = RedisManager()


async def create_admin_user():
    """Create default admin user if not exists"""
    try:
        # Check if admin user exists
        admin_user = await User.find_one(User.username == settings.admin_username)
        
        if not admin_user:
            logger.info("Creating default admin user...")
            
            from app.utils.auth import AuthUtils
            
            admin_user = User(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=AuthUtils.hash_password(settings.admin_password),
                first_name="Admin",
                last_name="User",
                is_verified=True,
                is_active=True,
            )
            
            await admin_user.insert()
            logger.info(f"Admin user created: {settings.admin_username}")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")


# Health check functions
async def check_mongodb_health() -> bool:
    """Check MongoDB connection health"""
    try:
        client = get_mongodb_client()
        await client.admin.command('ismaster')
        return True
    except Exception:
        return False


async def check_redis_health() -> bool:
    """Check Redis connection health"""
    try:
        redis = get_redis_async_client()
        await redis.ping()
        return True
    except Exception:
        return False


async def get_database_stats() -> dict:
    """Get database statistics"""
    try:
        stats = {}
        
        # MongoDB stats
        if await check_mongodb_health():
            stats['mongodb'] = {
                'connected': True,
                'users_count': await User.count(),
                'chats_count': await Chat.count(),
                'messages_count': await Message.count(),
                'notifications_count': await Notification.count(),
            }
        else:
            stats['mongodb'] = {'connected': False}
        
        # Redis stats
        if await check_redis_health():
            redis = get_redis_async_client()
            info = await redis.info()
            stats['redis'] = {
                'connected': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        else:
            stats['redis'] = {'connected': False}
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {'error': str(e)}