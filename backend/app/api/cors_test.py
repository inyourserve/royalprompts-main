"""
CORS Test endpoint for debugging
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/cors-test", tags=["CORS Test"])
async def cors_test():
    """Test endpoint to verify CORS configuration"""
    return JSONResponse(
        content={
            "message": "CORS test successful",
            "cors_configured": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@router.options("/cors-test", tags=["CORS Test"])
async def cors_test_options():
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={"message": "CORS preflight successful"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )
