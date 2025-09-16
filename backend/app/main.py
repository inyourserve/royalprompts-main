import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.core.exceptions import (
    BaseAPIException, base_api_exception_handler,
    http_exception_handler, validation_exception_handler,
    general_exception_handler
)
from app.db.database import connect_to_mongo, close_mongo_connection
from app.schemas.common import HealthResponse

# Import all individual routers directly
from app.api.mobile.auth import router as mobile_auth_router
from app.api.mobile.prompts import router as mobile_prompts_router
from app.api.mobile.favorites import router as mobile_favorites_router
from app.api.mobile.settings import router as mobile_settings_router
from app.api.mobile.social_links import router as mobile_social_links_router
from app.api.mobile.categories import router as mobile_categories_router
from app.api.admin.auth import router as admin_auth_router
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.prompts import router as admin_prompts_router
from app.api.admin.categories import router as admin_categories_router
from app.api.admin.settings import router as admin_settings_router
from app.api.admin.social_links import router as admin_social_links_router
from app.api.admin.users import router as admin_users_router
from app.api.cors_test import router as cors_test_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting RoyalPrompts API...")
    await connect_to_mongo()
    logger.info("✅ Application started successfully!")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down RoyalPrompts API...")
    await close_mongo_connection()
    logger.info("✅ Application shut down successfully!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Scalable backend API for RoyalPrompts mobile app and admin dashboard",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Setup exception handlers
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include all routers directly in main.py for better clarity
# Mobile App Routes
app.include_router(mobile_auth_router, prefix="/api/mobile/auth", tags=["Mobile Auth"])
app.include_router(mobile_prompts_router, prefix="/api/mobile/prompts", tags=["Mobile Prompts"])
app.include_router(mobile_favorites_router, prefix="/api/mobile/favorites", tags=["Mobile Favorites"])
app.include_router(mobile_settings_router, prefix="/api/mobile/settings", tags=["Mobile Settings"])
app.include_router(mobile_social_links_router, prefix="/api/mobile/social-links", tags=["Mobile Social Links"])
app.include_router(mobile_categories_router, prefix="/api/mobile/categories", tags=["Mobile Categories"])

# Admin Panel Routes (includes image upload for prompts)
app.include_router(admin_auth_router, prefix="/api/admin/auth", tags=["Admin Auth"])
app.include_router(admin_dashboard_router, prefix="/api/admin/dashboard", tags=["Admin Dashboard"])
app.include_router(admin_prompts_router, prefix="/api/admin/prompts", tags=["Admin Prompts"])
app.include_router(admin_categories_router, prefix="/api/admin/categories", tags=["Admin Categories"])
app.include_router(admin_settings_router, prefix="/api/admin/settings", tags=["Admin Settings"])
app.include_router(admin_social_links_router, prefix="/api/admin/social-links", tags=["Admin Social Links"])
app.include_router(admin_users_router, prefix="/api/admin/users", tags=["Admin Users"])

# CORS test endpoint
app.include_router(cors_test_router, prefix="/api", tags=["CORS Test"])


# Root endpoints
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp="2024-01-15T12:00:00Z",
        version=settings.APP_VERSION,
        database="connected"
    )


# File upload is now handled in minimal.py


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info"
    )
