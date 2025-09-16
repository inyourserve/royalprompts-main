# app/services/notification_channels.py

import logging
from datetime import datetime
from typing import Dict, Any, List

from app.db.models.database import motor_db
from app.services.firebase_service import get_firebase_service
from app.utils.websocket_manager import manager  # Your existing websocket manager

logger = logging.getLogger(__name__)


class NotificationChannels:
    """
    Handles different notification delivery channels
    Integrates with your existing WebSocket manager
    """

    def __init__(self):
        self.firebase_service = get_firebase_service()

    async def send_websocket(
            self,
            user_id: str,
            event_type: str,
            data: Dict[str, Any]
    ) -> bool:
        """
        Send notification via WebSocket using your existing manager
        Returns True if successful, False if failed
        """
        try:
            # OLD FORMAT - No timestamp, direct event type and data
            message = {
                "type": event_type,  # Use event type as-is (new_job, remove_job, etc.)
                "data": data
            }

            # Use your existing WebSocket manager's send_personal_message method
            await manager.send_personal_message(message, user_id)

            logger.debug(f"WebSocket sent to user {user_id}")
            return True

        except Exception as e:
            logger.debug(f"WebSocket failed for user {user_id}: {str(e)}")
            return False

    async def send_websocket_broadcast(
            self,
            event_type: str,
            data: Dict[str, Any],
            category_id: str = None,
            city_id: str = None
    ) -> bool:
        """
        Send WebSocket broadcast using your existing manager
        """
        try:
            # OLD FORMAT - No timestamp, direct event type and data
            message = {
                "type": event_type,  # Use event type as-is
                "data": data
            }

            # Use your existing broadcast method
            await manager.broadcast(
                message=message,
                category_id=category_id,
                city_id=city_id
            )

            logger.debug(f"WebSocket broadcast sent for category {category_id}, city {city_id}")
            return True

        except Exception as e:
            logger.error(f"WebSocket broadcast failed: {str(e)}")
            return False

    async def send_fcm(
            self,
            user_id: str,
            title: str,
            body: str,
            data: Dict[str, Any],
            target_app: str = "seeker"  # "provider" or "seeker"
    ) -> bool:
        """
        Send notification via FCM to specific app type
        Returns True if successful, False if failed
        """
        try:
            # Get user's FCM tokens for specific app type
            fcm_tokens = await self._get_user_fcm_tokens(user_id, target_app)

            if not fcm_tokens:
                logger.debug(f"No FCM tokens found for user {user_id}, app_type: {target_app}")
                return False

            # Prepare FCM data (all values must be strings)
            fcm_data = {
                **{k: str(v) for k, v in data.items()},
                "timestamp": datetime.utcnow().isoformat(),
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            }

            # Send FCM notification
            result = await self.firebase_service.send_notification(
                tokens=fcm_tokens,
                title=title,
                body=body,
                data=fcm_data
            )

            # Clean up failed tokens
            if result.get("failed_tokens"):
                await self._cleanup_failed_tokens(result["failed_tokens"])

            success = result.get("success", 0) > 0
            logger.debug(f"FCM sent to user {user_id}, app_type {target_app}: {success}")
            return success

        except Exception as e:
            logger.error(f"FCM failed for user {user_id}: {str(e)}")
            return False

    async def send_fcm_batch(
            self,
            user_ids: List[str],
            title: str,
            body: str,
            data: Dict[str, Any],
            target_app: str = "seeker"  # "provider" or "seeker"
    ) -> Dict[str, Any]:
        """
        Send FCM notifications to multiple users efficiently
        """
        try:
            # Collect all tokens for specific app type
            all_tokens = []
            token_user_map = {}

            for user_id in user_ids:
                user_tokens = await self._get_user_fcm_tokens(user_id, target_app)
                for token in user_tokens:
                    all_tokens.append(token)
                    token_user_map[token] = user_id

            if not all_tokens:
                return {
                    "success_count": 0,
                    "failure_count": len(user_ids),
                    "failed_users": user_ids
                }

            # Prepare FCM data
            fcm_data = {
                **{k: str(v) for k, v in data.items()},
                "timestamp": datetime.utcnow().isoformat(),
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            }

            # Send in batches of 500 (FCM limit)
            total_success = 0
            total_failure = 0
            failed_users = set()

            for i in range(0, len(all_tokens), 500):
                batch_tokens = all_tokens[i:i + 500]

                result = await self.firebase_service.send_notification(
                    tokens=batch_tokens,
                    title=title,
                    body=body,
                    data=fcm_data
                )

                total_success += result.get("success", 0)
                total_failure += result.get("failure", 0)

                # Track failed users
                if result.get("failed_tokens"):
                    for failed_token in result["failed_tokens"]:
                        failed_user = token_user_map.get(failed_token)
                        if failed_user:
                            failed_users.add(failed_user)

                    await self._cleanup_failed_tokens(result["failed_tokens"])

            return {
                "success_count": total_success,
                "failure_count": total_failure,
                "failed_users": list(failed_users),
                "total_tokens": len(all_tokens)
            }

        except Exception as e:
            logger.error(f"FCM batch send failed: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": len(user_ids),
                "failed_users": user_ids,
                "error": str(e)
            }

    async def _get_user_fcm_tokens(self, user_id: str, app_type: str = "seeker") -> List[str]:
        """Get active FCM tokens for a user and specific app type"""
        try:
            tokens = await motor_db.fcm_tokens.find({
                "user_id": user_id,
                "app_type": app_type,  # Filter by app type
                "is_active": True
            }).to_list(length=None)

            return [token["token"] for token in tokens if "token" in token]

        except Exception as e:
            logger.error(f"Error getting FCM tokens for user {user_id}, app_type {app_type}: {str(e)}")
            return []

    async def _cleanup_failed_tokens(self, failed_tokens: List[str]):
        """Mark failed FCM tokens as inactive"""
        try:
            await motor_db.fcm_tokens.update_many(
                {"token": {"$in": failed_tokens}},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            logger.info(f"Cleaned up {len(failed_tokens)} failed FCM tokens")
        except Exception as e:
            logger.error(f"Error cleaning up failed tokens: {str(e)}")

    # Future: Add email, SMS channels here
    async def send_email(self, user_id: str, subject: str, body: str) -> bool:
        """Future email channel implementation"""
        pass

    async def send_sms(self, user_id: str, message: str) -> bool:
        """Future SMS channel implementation"""
        pass

# #old app/services/notification_channels.py
#
# import logging
# from datetime import datetime
# from typing import Dict, Any, List
#
# from app.db.models.database import motor_db
# from app.services.firebase_service import get_firebase_service
# from app.utils.websocket_manager import manager  # Your existing websocket manager
#
# logger = logging.getLogger(__name__)
#
#
# class NotificationChannels:
#     """
#     Handles different notification delivery channels
#     Integrates with your existing WebSocket manager
#     """
#
#     def __init__(self):
#         self.firebase_service = get_firebase_service()
#
#     async def send_websocket(
#             self,
#             user_id: str,
#             event_type: str,
#             data: Dict[str, Any]
#     ) -> bool:
#         """
#         Send notification via WebSocket using your existing manager
#         Returns True if successful, False if failed
#         """
#         try:
#             message = {
#                 "type": event_type.lower(),  # Convert NEW_JOB to new_job for consistency
#                 "data": data,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#
#             # Use your existing WebSocket manager's send_personal_message method
#             await manager.send_personal_message(message, user_id)
#
#             logger.debug(f"WebSocket sent to user {user_id}")
#             return True
#
#         except Exception as e:
#             logger.debug(f"WebSocket failed for user {user_id}: {str(e)}")
#             return False
#
#     async def send_websocket_broadcast(
#             self,
#             event_type: str,
#             data: Dict[str, Any],
#             category_id: str = None,
#             city_id: str = None
#     ) -> bool:
#         """
#         Send WebSocket broadcast using your existing manager
#         """
#         try:
#             message = {
#                 "type": event_type.lower(),
#                 "data": data,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#
#             # Use your existing broadcast method
#             await manager.broadcast(
#                 message=message,
#                 category_id=category_id,
#                 city_id=city_id
#             )
#
#             logger.debug(f"WebSocket broadcast sent for category {category_id}, city {city_id}")
#             return True
#
#         except Exception as e:
#             logger.error(f"WebSocket broadcast failed: {str(e)}")
#             return False
#
#     async def send_fcm(
#             self,
#             user_id: str,
#             title: str,
#             body: str,
#             data: Dict[str, Any],
#             target_app: str = "seeker"  # "provider" or "seeker"
#     ) -> bool:
#         """
#         Send notification via FCM to specific app type
#         Returns True if successful, False if failed
#         """
#         try:
#             # Get user's FCM tokens for specific app type
#             fcm_tokens = await self._get_user_fcm_tokens(user_id, target_app)
#
#             if not fcm_tokens:
#                 logger.debug(f"No FCM tokens found for user {user_id}, app_type: {target_app}")
#                 return False
#
#             # Prepare FCM data (all values must be strings)
#             fcm_data = {
#                 **{k: str(v) for k, v in data.items()},
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "click_action": "FLUTTER_NOTIFICATION_CLICK"
#             }
#
#             # Send FCM notification
#             result = await self.firebase_service.send_notification(
#                 tokens=fcm_tokens,
#                 title=title,
#                 body=body,
#                 data=fcm_data
#             )
#
#             # Clean up failed tokens
#             if result.get("failed_tokens"):
#                 await self._cleanup_failed_tokens(result["failed_tokens"])
#
#             success = result.get("success", 0) > 0
#             logger.debug(f"FCM sent to user {user_id}, app_type {target_app}: {success}")
#             return success
#
#         except Exception as e:
#             logger.error(f"FCM failed for user {user_id}: {str(e)}")
#             return False
#
#     async def send_fcm_batch(
#             self,
#             user_ids: List[str],
#             title: str,
#             body: str,
#             data: Dict[str, Any],
#             target_app: str = "seeker"  # "provider" or "seeker"
#     ) -> Dict[str, Any]:
#         """
#         Send FCM notifications to multiple users efficiently
#         """
#         try:
#             # Collect all tokens for specific app type
#             all_tokens = []
#             token_user_map = {}
#
#             for user_id in user_ids:
#                 user_tokens = await self._get_user_fcm_tokens(user_id, target_app)
#                 for token in user_tokens:
#                     all_tokens.append(token)
#                     token_user_map[token] = user_id
#
#             if not all_tokens:
#                 return {
#                     "success_count": 0,
#                     "failure_count": len(user_ids),
#                     "failed_users": user_ids
#                 }
#
#             # Prepare FCM data
#             fcm_data = {
#                 **{k: str(v) for k, v in data.items()},
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "click_action": "FLUTTER_NOTIFICATION_CLICK"
#             }
#
#             # Send in batches of 500 (FCM limit)
#             total_success = 0
#             total_failure = 0
#             failed_users = set()
#
#             for i in range(0, len(all_tokens), 500):
#                 batch_tokens = all_tokens[i:i + 500]
#
#                 result = await self.firebase_service.send_notification(
#                     tokens=batch_tokens,
#                     title=title,
#                     body=body,
#                     data=fcm_data
#                 )
#
#                 total_success += result.get("success", 0)
#                 total_failure += result.get("failure", 0)
#
#                 # Track failed users
#                 if result.get("failed_tokens"):
#                     for failed_token in result["failed_tokens"]:
#                         failed_user = token_user_map.get(failed_token)
#                         if failed_user:
#                             failed_users.add(failed_user)
#
#                     await self._cleanup_failed_tokens(result["failed_tokens"])
#
#             return {
#                 "success_count": total_success,
#                 "failure_count": total_failure,
#                 "failed_users": list(failed_users),
#                 "total_tokens": len(all_tokens)
#             }
#
#         except Exception as e:
#             logger.error(f"FCM batch send failed: {str(e)}")
#             return {
#                 "success_count": 0,
#                 "failure_count": len(user_ids),
#                 "failed_users": user_ids,
#                 "error": str(e)
#             }
#
#     async def _get_user_fcm_tokens(self, user_id: str, app_type: str = "seeker") -> List[str]:
#         """Get active FCM tokens for a user and specific app type"""
#         try:
#             tokens = await motor_db.fcm_tokens.find({
#                 "user_id": user_id,
#                 "app_type": app_type,  # Filter by app type
#                 "is_active": True
#             }).to_list(length=None)
#
#             return [token["token"] for token in tokens if "token" in token]
#
#         except Exception as e:
#             logger.error(f"Error getting FCM tokens for user {user_id}, app_type {app_type}: {str(e)}")
#             return []
#
#     async def _cleanup_failed_tokens(self, failed_tokens: List[str]):
#         """Mark failed FCM tokens as inactive"""
#         try:
#             await motor_db.fcm_tokens.update_many(
#                 {"token": {"$in": failed_tokens}},
#                 {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
#             )
#             logger.info(f"Cleaned up {len(failed_tokens)} failed FCM tokens")
#         except Exception as e:
#             logger.error(f"Error cleaning up failed tokens: {str(e)}")
#
#     # Future: Add email, SMS channels here
#     async def send_email(self, user_id: str, subject: str, body: str) -> bool:
#         """Future email channel implementation"""
#         # TODO: Implement email sending
#         pass
#
#     async def send_sms(self, user_id: str, message: str) -> bool:
#         """Future SMS channel implementation"""
#         # TODO: Implement SMS sending
#         pass
