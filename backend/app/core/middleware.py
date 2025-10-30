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
    """Smart rate limiting middleware with different limits for different endpoints"""
    
    def __init__(self, app):
        super().__init__(app)
        self.clients = {}
        
        # Define rate limits for different endpoint types
        self.rate_limits = {
            # Mobile API - Very generous (users browsing, favoriting prompts)
            "/api/mobile": {"calls": 5000, "period": 60},  # 5000 requests/min for mobile users
            
            # Admin API - Moderate limits (fewer admins, CRUD operations)
            "/api/admin": {"calls": 500, "period": 60},  # 500 requests/min for admins
            
            # Authentication - Strict (prevent brute force)
            "/api/auth": {"calls": 20, "period": 60},  # 20 login attempts per minute
            
            # Default for other endpoints
            "default": {"calls": 1000, "period": 60}
        }
        
        # Paths to exclude from rate limiting entirely
        self.exclude_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/"]
    
    def get_rate_limit(self, path: str) -> dict:
        """Get rate limit configuration for a given path"""
        for prefix, limit in self.rate_limits.items():
            if path.startswith(prefix):
                return limit
        return self.rate_limits["default"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Skip rate limiting for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Get rate limit for this endpoint
        rate_limit = self.get_rate_limit(path)
        max_calls = rate_limit["calls"]
        period = rate_limit["period"]
        
        # Get real client IP from X-Forwarded-For header (from Nginx proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Create unique key for this IP + path prefix
        rate_limit_key = f"{client_ip}:{path.split('/')[1] if '/' in path else 'root'}"
        current_time = time.time()
        
        # Clean old entries (older than period)
        self.clients = {
            key: (calls, start_time) 
            for key, (calls, start_time) in self.clients.items()
            if current_time - start_time < period
        }
        
        # Check rate limit
        if rate_limit_key in self.clients:
            calls_made, start_time = self.clients[rate_limit_key]
            if current_time - start_time < period:
                if calls_made >= max_calls:
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Max {max_calls} requests per {period} seconds for this endpoint."
                    )
                self.clients[rate_limit_key] = (calls_made + 1, start_time)
            else:
                self.clients[rate_limit_key] = (1, current_time)
        else:
            self.clients[rate_limit_key] = (1, current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers for transparency
        current_calls = self.clients.get(rate_limit_key, (0, 0))[0]
        response.headers["X-RateLimit-Limit"] = str(max_calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_calls - current_calls))
        response.headers["X-RateLimit-Reset"] = str(int(self.clients.get(rate_limit_key, (0, current_time))[1] + period))
        
        return response


def setup_middleware(app):
    """Setup all middleware for the application"""
    
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
        # Smart rate limiting with different limits per endpoint type
        app.add_middleware(RateLimitMiddleware)
