# app/api/v1/dependencies/admin_auth.py
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_admin(api_key: str = Depends(api_key_header)):
    """Extract and validate the current admin using JWT."""
    # Print for debugging
    print(f"Received Authorization Header: {api_key}")

    # Handle cases where no token is provided
    if not api_key:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Check if token starts with Bearer
    if not api_key.startswith("Bearer "):
        # If it doesn't start with Bearer, try to use as-is (for backward compatibility)
        token = api_key
    else:
        # Remove "Bearer " prefix
        token = api_key.split(" ", 1)[1]

    try:
        # Decode token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Extract user information
        user_id = payload.get("user_id")
        email = payload.get("email")

        # Extract full role structure
        role = payload.get("role", {})

        # Validate required claims
        if not user_id or not role:
            raise HTTPException(status_code=400, detail="Invalid token payload")

        return {
            "user_id": user_id,
            "email": email,
            "role": role,  # Return the full role structure
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token decoding error: {e}")
        raise HTTPException(status_code=500, detail="Error decoding token")
