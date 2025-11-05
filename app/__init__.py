"""
ChatX API - Real-Time Messaging Backend
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_database, close_database, create_admin_user
from app.routes import auth, users, chats, messages

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)



# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Real-Time Messaging Backend API with FastAPI, MongoDB, and Redis",
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


@app.on_event("startup")
async def startup_event():
    """Handle application startup"""
    logger.info("=== ChatX API STARTUP BEGIN ===")
    
    try:
        # Initialize database connections
        logger.info("Initializing database connections...")
        await init_database()
        logger.info("✅ Database initialization completed")
        
        # Create admin user if not exists
        logger.info("Setting up admin user...")
        await create_admin_user()
        logger.info("✅ Admin user setup completed")
        
        logger.info("🚀 ChatX API startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start ChatX API: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown"""
    logger.info("=== ChatX API SHUTDOWN BEGIN ===")
    try:
        await close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
    
    logger.info("✅ ChatX API shutdown completed")

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add validation error handler for debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print(f"❌ Validation Error on {request.method} {request.url}")
    print(f"❌ Request body: {body}")
    print(f"❌ Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body.decode('utf-8') if body else None,
            "debug_info": "Check server logs for more details"
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database status"""
    from app.database import get_database_stats
    
    try:
        db_stats = await get_database_stats()
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "database": db_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


@app.get("/test-register")
async def test_register():
    """Test registration endpoint"""
    from app.database.schemas.models import UserRegisterRequest
    from app.routes.auth import register_user
    
    # Test user data
    test_user = UserRegisterRequest(
        username="Naval12",
        email="naval@gmail.com",
        password="12345678",
        first_name="naval",
        last_name="jha",
        phone="9508154648"
    )
    
    try:
        result = await register_user(test_user)
        return {"status": "success", "result": result}
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }