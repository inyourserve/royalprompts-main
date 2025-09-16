import jwt
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_user(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = api_key.split(" ")[1] if api_key.startswith("Bearer ") else api_key

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        mobile: str = payload.get("mobile")
        user_id: str = payload.get("user_id")
        roles: list = payload.get("roles", [])

        if mobile is None or not roles:
            raise HTTPException(status_code=400, detail="Invalid token")

        return {"user_id": user_id, "mobile": mobile, "roles": roles}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
