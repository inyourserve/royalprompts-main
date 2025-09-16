# app/services/firebase_service.py
import json
import logging
import os
from typing import Dict, List

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase service for Workerlly notifications"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                # Try environment variable first (for Docker/CI/CD)
                firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")
                if firebase_creds:
                    # Parse JSON from environment variable
                    cred_dict = json.loads(firebase_creds)
                    cred = credentials.Certificate(cred_dict)
                    logger.info("Firebase initialized from environment variable")
                else:
                    # Fallback to file path (for local development)
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                    logger.info("Firebase initialized from file path")

                firebase_admin.initialize_app(cred)
                self._initialized = True
                logger.info("Firebase initialized successfully for Workerlly")
            except Exception as e:
                logger.error(f"Firebase initialization failed: {str(e)}")
                raise e

    async def send_notification(
            self, tokens: List[str], title: str, body: str, data: Dict = None
    ) -> Dict:
        """
        Send heads-up FCM notification to multiple tokens with routing support
        """
        if not tokens:
            return {"success": 0, "failure": 0}

        try:
            # Prepare data - all values must be strings for FCM
            notification_data = {k: str(v) for k, v in (data or {}).items()}

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=notification_data,
                tokens=tokens,

                # HEADS-UP ANDROID CONFIG
                android=messaging.AndroidConfig(
                    priority="high",  # Required for heads-up
                    notification=messaging.AndroidNotification(
                        title=title,  # Required for heads-up
                        body=body,  # Required for heads-up
                        click_action="FLUTTER_NOTIFICATION_CLICK",
                        channel_id="workerlly_urgent_jobs",  # High priority channel
                        sound="default",
                        priority="high",  # Force heads-up display
                        visibility="public",  # Show on lock screen
                        color="#FF6B35",  # Your brand color (optional)
                        icon="ic_notification"  # Your notification icon (optional)
                    ),
                    # Time to live - keeps notification for 1 hour if device offline
                    ttl=3600
                ),

                # HEADS-UP iOS CONFIG
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10"},  # High priority for heads-up
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(title=title, body=body),
                            content_available=True,
                            badge=1,
                            sound="default",
                            mutable_content=True  # Allow rich content
                        )
                    )
                )
            )

            response = messaging.send_each_for_multicast(message)

            result = {
                "success": response.success_count,
                "failure": response.failure_count
            }

            # Track failed tokens for cleanup
            if response.failure_count > 0:
                failed_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
                        logger.debug(f"FCM failed for token {tokens[idx]}: {resp.exception}")
                result["failed_tokens"] = failed_tokens

            logger.info(f"FCM batch sent: {response.success_count} success, {response.failure_count} failed")
            return result

        except Exception as e:
            logger.error(f"FCM send error: {str(e)}")
            return {"success": 0, "failure": len(tokens), "error": str(e)}


# Singleton
def get_firebase_service() -> FirebaseService:
    return FirebaseService()
