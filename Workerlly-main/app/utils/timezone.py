import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

DEFAULT_TIMEZONE = ZoneInfo("Asia/Kolkata")


class TimezoneHandler:
    @staticmethod
    def from_utc(dt_str: str, tz: ZoneInfo) -> str:
        try:
            # Convert string to datetime object
            dt = datetime.fromisoformat(dt_str)
            # Ensure the datetime is treated as UTC if tzinfo is missing
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # Convert to the target timezone
            return dt.astimezone(tz).isoformat()
        except ValueError:
            # Return the string unchanged if it's not a valid datetime
            return dt_str

    @classmethod
    def convert_dict(cls, data: Any, target_tz: ZoneInfo) -> Any:
        if isinstance(data, dict):
            return {
                key: cls.convert_dict(value, target_tz) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [cls.convert_dict(item, target_tz) for item in data]
        elif isinstance(data, str) and "T" in data:
            # Handle ISO-8601 datetime strings
            return cls.from_utc(data, target_tz)
        return data


class TimezoneMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        if response.headers.get("content-type") == "application/json":
            body = [
                section async for section in response.body_iterator
            ]  # Read the response body
            try:
                body = b"".join(body).decode("utf-8")  # Join and decode body sections
                data = json.loads(body)  # Parse JSON
                converted_data = TimezoneHandler.convert_dict(
                    data, DEFAULT_TIMEZONE
                )  # Convert timezone

                # Remove the Content-Length header as the body has changed
                headers = dict(response.headers)
                headers.pop(
                    "content-length", None
                )  # Remove content-length to let it recalculate

                return JSONResponse(
                    content=converted_data,  # Return the modified response
                    status_code=response.status_code,
                    headers=headers,  # Use modified headers without content-length
                )
            except (json.JSONDecodeError, ValueError):
                pass

        return response
