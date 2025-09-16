# app/api/v1/endpoints/notifications.py

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.services.notification_analytics import NotificationAnalytics

router = APIRouter()
logger = logging.getLogger(__name__)


class FCMTokenRequest(BaseModel):
    token: str
    device_id: str
    platform: str  # "android" or "ios"
    app_type: str  # "provider" or "seeker"
    app_version: Optional[str] = None
    device_model: Optional[str] = None


class FCMTokenResponse(BaseModel):
    success: bool
    message: str


@router.post("/fcm/register", response_model=FCMTokenResponse)
async def register_fcm_token(
        token_request: FCMTokenRequest,
        current_user: dict = Depends(get_current_user)
):
    """
    Register FCM token for push notifications
    """
    try:
        user_id = current_user["user_id"]

        # Validate app_type
        if token_request.app_type not in ["provider", "seeker"]:
            raise HTTPException(status_code=400, detail="app_type must be 'provider' or 'seeker'")

        # Upsert FCM token
        await motor_db.fcm_tokens.update_one(
            {
                "user_id": user_id,
                "device_id": token_request.device_id,
                "app_type": token_request.app_type
            },
            {
                "$set": {
                    "token": token_request.token,
                    "platform": token_request.platform,
                    "app_type": token_request.app_type,
                    "app_version": token_request.app_version,
                    "device_model": token_request.device_model,
                    "is_active": True,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"FCM token registered for user {user_id}, app_type: {token_request.app_type}")
        return FCMTokenResponse(success=True, message="Token registered successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering FCM token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register token")


@router.delete("/fcm/unregister")
async def unregister_fcm_token(
        device_id: str,
        app_type: str,
        current_user: dict = Depends(get_current_user)
):
    """
    Unregister FCM token
    """
    try:
        user_id = current_user["user_id"]

        result = await motor_db.fcm_tokens.update_one(
            {
                "user_id": user_id,
                "device_id": device_id,
                "app_type": app_type
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Token not found")

        return FCMTokenResponse(success=True, message="Token unregistered successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering FCM token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unregister token")


@router.get("/analytics/stats")
async def get_notification_stats(
        days: int = Query(30, description="Number of days to look back"),
        event_type: Optional[str] = Query(None, description="Filter by event type"),
        current_user: dict = Depends(get_current_user)
):
    """
    Get notification delivery statistics
    """
    try:
        # Check if user has admin role (adjust based on your role system)
        user_roles = current_user.get("roles", [])
        if "admin" not in user_roles and "provider" not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")

        analytics = NotificationAnalytics()

        # Get date range
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        stats = await analytics.get_stats(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/analytics/daily")
async def get_daily_notification_stats(
        days: int = Query(7, description="Number of days"),
        current_user: dict = Depends(get_current_user)
):
    """
    Get daily breakdown of notification statistics
    """
    try:
        # Check permissions
        user_roles = current_user.get("roles", [])
        if "admin" not in user_roles and "provider" not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")

        analytics = NotificationAnalytics()
        daily_stats = await analytics.get_daily_stats(days=days)

        return {"daily_stats": daily_stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get daily statistics")
