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
app.mount("/uploads", StaticFiles(directory=settings.upload_dir_path), name="uploads")

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


# Debug endpoints for file system troubleshooting
@app.get("/debug/files", tags=["Debug"])
async def debug_files():
    """Debug endpoint to check file system"""
    import os
    
    upload_dir = settings.upload_dir_path
    
    def list_files_in_dir(directory):
        try:
            if os.path.exists(directory):
                files = os.listdir(directory)
                return {
                    "exists": True,
                    "files": files,
                    "file_count": len(files),
                    "absolute_path": os.path.abspath(directory)
                }
            else:
                return {"exists": False, "absolute_path": os.path.abspath(directory)}
        except Exception as e:
            return {"error": str(e), "absolute_path": os.path.abspath(directory)}
    
    return {
        "upload_dir": upload_dir,
        "upload_dir_info": list_files_in_dir(upload_dir),
        "images_dir": list_files_in_dir(f"{upload_dir}/images"),
        "thumbnails_dir": list_files_in_dir(f"{upload_dir}/thumbnails"),
        "temp_dir": list_files_in_dir(f"{upload_dir}/temp"),
        "current_working_directory": os.getcwd(),
        "settings_info": {
            "upload_dir": settings.UPLOAD_DIR,
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION
        }
    }


@app.get("/debug/test-image/{filename}", tags=["Debug"])
async def test_specific_image(filename: str):
    """Test if a specific image file exists and is accessible"""
    import os
    
    upload_dir = settings.upload_dir_path
    image_path = os.path.join(upload_dir, "images", filename)
    temp_path = os.path.join(upload_dir, "temp", filename)
    
    return {
        "filename": filename,
        "images_path": image_path,
        "temp_path": temp_path,
        "images_exists": os.path.exists(image_path),
        "temp_exists": os.path.exists(temp_path),
        "upload_dir": upload_dir,
        "expected_images_url": f"/uploads/images/{filename}",
        "expected_temp_url": f"/uploads/temp/{filename}",
        "file_size_images": os.path.getsize(image_path) if os.path.exists(image_path) else None,
        "file_size_temp": os.path.getsize(temp_path) if os.path.exists(temp_path) else None
    }


@app.get("/debug/upload-stats", tags=["Debug"])
async def upload_stats():
    """Get upload directory statistics"""
    import os
    
    upload_dir = settings.upload_dir_path
    
    def get_dir_stats(directory):
        try:
            if os.path.exists(directory):
                files = os.listdir(directory)
                total_size = 0
                file_details = []
                
                for file in files:
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        total_size += size
                        file_details.append({
                            "name": file,
                            "size": size,
                            "size_mb": round(size / (1024 * 1024), 2)
                        })
                
                return {
                    "exists": True,
                    "file_count": len(files),
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "files": file_details
                }
            else:
                return {"exists": False}
        except Exception as e:
            return {"error": str(e)}
    
    return {
        "upload_dir": upload_dir,
        "images_stats": get_dir_stats(f"{upload_dir}/images"),
        "thumbnails_stats": get_dir_stats(f"{upload_dir}/thumbnails"),
        "temp_stats": get_dir_stats(f"{upload_dir}/temp"),
        "total_upload_dir_stats": get_dir_stats(upload_dir)
    }


@app.post("/debug/cleanup-temp", tags=["Debug"])
async def cleanup_temp_files():
    """Clean up temporary files (for testing purposes)"""
    import os
    import shutil
    
    upload_dir = settings.upload_dir_path
    temp_dir = f"{upload_dir}/temp"
    
    try:
        if os.path.exists(temp_dir):
            files = os.listdir(temp_dir)
            for file in files:
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            return {
                "success": True,
                "message": f"Cleaned up {len(files)} temporary files",
                "temp_dir": temp_dir
            }
        else:
            return {
                "success": True,
                "message": "Temp directory doesn't exist",
                "temp_dir": temp_dir
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "temp_dir": temp_dir
        }


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
