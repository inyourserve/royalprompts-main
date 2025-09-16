# import json
# import logging
# from datetime import datetime, timedelta
#
# from bson import ObjectId
#
# from app.core.config import settings
# from app.db.models.database import motor_db
# from app.utils.redis_manager import RedisManager
#
# logger = logging.getLogger(__name__)
#
#
# class RedisService:
#     def __init__(self, redis_manager: RedisManager):
#         self.redis_manager = redis_manager
#
#     async def remove_job_notification(self, job_id: str, category_id: str, city_id: str):
#         redis_key = f"job_notifications:{category_id}:{city_id}"
#         try:
#             # Get all notifications from the sorted set
#             notifications = await self.redis_manager.zrange(
#                 redis_key, 0, -1, withscores=False
#             )
#
#             for notification in notifications:
#                 notification_data = json.loads(notification)
#                 if notification_data["data"]["id"] == job_id:
#                     # Remove this specific notification
#                     await self.redis_manager.zrem(redis_key, notification)
#                     logger.info(f"Removed job notification for job {job_id} from Redis")
#                     break
#         except Exception as e:
#             logger.error(f"Failed to remove job notification from Redis: {str(e)}")
#
#     async def store_job_notification(self, job_data: dict):
#         notification_data = {
#             "type": "new_job",
#             "data": {
#                 "id": str(job_data["_id"]),
#                 "sub_category": await get_sub_category_name(
#                     job_data["sub_category_ids"][0]
#                 ),
#                 "location": f"{job_data['address_snapshot']['label']}, {await get_city_name(job_data['address_snapshot']['city_id'])}",
#                 "hourly_rate": job_data["hourly_rate"],
#             },
#         }
#         redis_key = f"job_notifications:{str(job_data['category_id'])}:{str(job_data['address_snapshot']['city_id'])}"
#         try:
#             await self.redis_manager.zadd(
#                 redis_key,
#                 {json.dumps(notification_data): int(datetime.utcnow().timestamp())},
#             )
#             await self.redis_manager.expire(redis_key, settings.JOB_CACHE_EXPIRY)
#             logger.info(f"Stored job notification in Redis for job {job_data['_id']}")
#
#             # Schedule job for relay
#             await self.schedule_job_relay(
#                 job_data["_id"],
#                 notification_data,
#                 job_data["category_id"],
#                 job_data["address_snapshot"]["city_id"],
#             )
#         except Exception as e:
#             logger.error(f"Failed to store job notification in Redis: {str(e)}")
#
#     async def schedule_job_relay(self, job_id: str, notification_data: dict, category_id: str, city_id: str):
#         relay_time = datetime.utcnow() + timedelta(minutes=1)
#         relay_key = f"job_relay:{job_id}"
#
#         # Convert ObjectId to string before storing
#         relay_data = {
#             "notification": notification_data,
#             "category_id": str(category_id),  # Convert to string if it's an ObjectId
#             "city_id": str(city_id),  # Convert to string if it's an ObjectId
#         }
#         try:
#             # Set the key without expiration
#             await self.redis_manager.set(
#                 relay_key, json.dumps(relay_data)
#             )
#
#             # Set expiration separately
#             await self.redis_manager.expire(relay_key, 120)  # Expire in 2 minutes
#
#             logger.info(f"Scheduled job {job_id} for relay at {relay_time}")
#         except Exception as e:
#             logger.error(f"Failed to schedule job relay in Redis: {str(e)}")
#
#     async def get_recent_job_notifications(self, redis_key: str):
#         try:
#             notifications = await self.redis_manager.zrange(
#                 redis_key, 0, -1, desc=True, withscores=False
#             )
#             return [json.loads(notification) for notification in notifications]
#         except Exception as e:
#             logger.error(f"Failed to get recent job notifications from Redis: {str(e)}")
#             return []
#
#     # Add other Redis-related methods here as needed
#
#
# redis_service = None
#
#
# def get_redis_service(redis_manager: RedisManager):
#     global redis_service
#     if redis_service is None:
#         redis_service = RedisService(redis_manager)
#     return redis_service
#
#
# async def get_sub_category_name(sub_category_id: ObjectId) -> str:
#     category = await motor_db.categories.find_one(
#         {"sub_categories.id": sub_category_id}, {"sub_categories.$": 1}
#     )
#     if category and "sub_categories" in category:
#         sub_category = category["sub_categories"][0]
#         return sub_category["name"]
#     return "Unknown Sub Category"
#
#
# async def get_city_name(city_id: ObjectId) -> str:
#     city = await motor_db.cities.find_one({"_id": city_id})
#     return city["name"] if city else "Unknown City"

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from app.core.config import settings
from app.db.models.database import motor_db
from app.utils.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager

    async def remove_job_notification(
        self, job_id: str, category_id: str, city_id: str
    ):
        redis_key = f"job_notifications:{category_id}:{city_id}"
        try:
            # Get all notifications from the sorted set
            notifications = await self.redis_manager.zrange(
                redis_key, 0, -1, withscores=False
            )

            for notification in notifications:
                notification_data = json.loads(notification)
                if notification_data["data"]["id"] == job_id:
                    # Remove this specific notification
                    await self.redis_manager.zrem(redis_key, notification)
                    logger.info(f"Removed job notification for job {job_id} from Redis")
                    break
        except Exception as e:
            logger.error(f"Failed to remove job notification from Redis: {str(e)}")

    async def store_job_notification(self, job_data: dict, user_id: str = None):
        notification_data = {
            "type": "new_job",
            "data": {
                "id": str(job_data["_id"]),
                "sub_category": await get_sub_category_name(
                    job_data["sub_category_ids"][0]
                ),
                "location": f"{job_data['address_snapshot']['label']}, {await get_city_name(job_data['address_snapshot']['city_id'])}",
                "hourly_rate": job_data["hourly_rate"],
                "user_id": (
                    str(user_id) if user_id else None
                ),  # Add user_id to the notification data
            },
        }
        redis_key = f"job_notifications:{str(job_data['category_id'])}:{str(job_data['address_snapshot']['city_id'])}"
        try:
            await self.redis_manager.zadd(
                redis_key,
                {json.dumps(notification_data): int(datetime.utcnow().timestamp())},
            )
            await self.redis_manager.expire(redis_key, settings.JOB_CACHE_EXPIRY)
            logger.info(f"Stored job notification in Redis for job {job_data['_id']}")

            # Schedule job for relay
            await self.schedule_job_relay(
                job_data["_id"],
                notification_data,
                job_data["category_id"],
                job_data["address_snapshot"]["city_id"],
            )
        except Exception as e:
            logger.error(f"Failed to store job notification in Redis: {str(e)}")

    async def schedule_job_relay(
        self, job_id: str, notification_data: dict, category_id: str, city_id: str
    ):
        relay_time = datetime.utcnow() + timedelta(minutes=1)
        relay_key = f"job_relay:{job_id}"

        # Convert ObjectId to string before storing
        relay_data = {
            "notification": notification_data,
            "category_id": str(category_id),  # Convert to string if it's an ObjectId
            "city_id": str(city_id),  # Convert to string if it's an ObjectId
        }
        try:
            # Set the key without expiration
            await self.redis_manager.set(relay_key, json.dumps(relay_data))

            # Set expiration separately
            await self.redis_manager.expire(relay_key, 120)  # Expire in 2 minutes

            logger.info(f"Scheduled job {job_id} for relay at {relay_time}")
        except Exception as e:
            logger.error(f"Failed to schedule job relay in Redis: {str(e)}")

    async def get_recent_job_notifications(self, redis_key: str):
        try:
            notifications = await self.redis_manager.zrange(
                redis_key, 0, -1, desc=True, withscores=False
            )
            return [json.loads(notification) for notification in notifications]
        except Exception as e:
            logger.error(f"Failed to get recent job notifications from Redis: {str(e)}")
            return []

    # Add this to RedisService class
    async def get_job_id_by_user_id(self, user_id: str) -> Optional[str]:
        """
        Get job_id from sorted set by matching user_id using pattern matching
        """
        try:
            # Search in all job_notifications keys
            keys = await self.redis_manager.keys("job_notifications:*")

            # Check each key
            for key in keys:
                notifications = await self.redis_manager.zrange(
                    key, 0, -1, desc=True, withscores=False
                )

                # Find job_id by matching user_id
                for notif in notifications:
                    data = json.loads(notif)
                    if data["data"]["user_id"] == user_id:
                        logger.info(
                            f"Found job_id for user {user_id}: {data['data']['id']}"
                        )
                        return data["data"]["id"]

            logger.info(f"No job found for user {user_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get job_id from Redis: {str(e)}")
            return None


redis_service = None


def get_redis_service(redis_manager: RedisManager):
    global redis_service
    if redis_service is None:
        redis_service = RedisService(redis_manager)
    return redis_service


async def get_sub_category_name(sub_category_id: ObjectId) -> str:
    category = await motor_db.categories.find_one(
        {"sub_categories.id": sub_category_id}, {"sub_categories.$": 1}
    )
    if category and "sub_categories" in category:
        sub_category = category["sub_categories"][0]
        return sub_category["name"]
    return "Unknown Sub Category"


async def get_city_name(city_id: ObjectId) -> str:
    city = await motor_db.cities.find_one({"_id": city_id})
    return city["name"] if city else "Unknown City"
