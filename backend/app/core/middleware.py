import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Processing time: {process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: (calls, start_time) 
            for ip, (calls, start_time) in self.clients.items()
            if current_time - start_time < self.period
        }
        
        # Check rate limit
        if client_ip in self.clients:
            calls_made, start_time = self.clients[client_ip]
            if current_time - start_time < self.period:
                if calls_made >= self.calls:
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
                self.clients[client_ip] = (calls_made + 1, start_time)
            else:
                self.clients[client_ip] = (1, current_time)
        else:
            self.clients[client_ip] = (1, current_time)
        
        response = await call_next(request)
        return response


def setup_middleware(app):
    """Setup all middleware for the application"""
    
    # Log CORS configuration
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request logging middleware
    if settings.DEBUG:
        app.add_middleware(RequestLoggingMiddleware)
    
    # Add rate limiting middleware (only in production)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(RateLimitMiddleware, calls=100, period=60)
