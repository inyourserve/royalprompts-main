import asyncio
import json
import logging

from redis.asyncio import Redis

from app.core.config import settings
from app.utils.websocket_manager import manager

logger = logging.getLogger(__name__)

redis_password = settings.REDIS_PASSWORD
redis_host = settings.REDIS_HOST
redis_port = settings.REDIS_PORT

REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}"


class RedisSubscriber:
    def __init__(self):
        self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.redis.pubsub()

    async def subscribe(self):
        """Subscribe to Redis key expiration events."""
        try:
            await self.pubsub.psubscribe("__keyevent@0__:expired")
            logger.info("Subscribed to Redis key expiration events")
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis events: {str(e)}")

    async def listen(self):
        """Start listening to key expiration events."""
        await self.subscribe()
        try:
            while True:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=False, timeout=1
                )

                if message:
                    # Check if the message is a subscription acknowledgment
                    if message.get("type") == "psubscribe":
                        logger.info(
                            f"Subscribed to pattern: {message['channel']} with count: {message['data']}"
                        )
                    # Handle other messages
                    else:
                        await self.handle_message(message)

                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Shutting down Redis subscriber.")
            await self.pubsub.unsubscribe()
            await self.redis.close()

    async def handle_message(self, message):
        """Handle the expired key message from Redis."""
        try:
            logger.debug(f"Received message from Redis: {message}")

            if message["channel"] == "__keyevent@0__:expired":
                key = message["data"]
                logger.debug(f"Key expired: {key}")

                # Handling job_relay expiration
                if key.startswith("job_relay:"):
                    job_id = key.split(":")[1]
                    logger.debug(f"Handling job relay for job {job_id}")

                    # Fetch category_id and city_id for the job from Redis
                    category_id = await self.redis.get(f"job_category:{job_id}")
                    city_id = await self.redis.get(f"job_city:{job_id}")

                    # Check if the job data is available
                    if not category_id or not city_id:
                        logger.error(f"Missing category_id or city_id for job {job_id}")
                        return

                    redis_key = f"job_notifications:{category_id}:{city_id}"

                    # Retrieve all notifications for the category and city
                    notifications = await self.redis.zrange(redis_key, 0, -1)

                    if not notifications:
                        logger.warning(
                            f"No notifications found in Redis for category {category_id} and city {city_id}"
                        )

                    for notification in notifications:
                        notification_data = json.loads(notification)
                        if notification_data["data"]["id"] == job_id:
                            await manager.broadcast(
                                notification_data["data"],
                                category_id=category_id,
                                city_id=city_id,
                            )
                            logger.info(f"Relayed job {job_id} after 2 minutes")
                            break
                    else:
                        logger.warning(f"Notification not found for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to handle message: {str(e)}")


redis_subscriber = RedisSubscriber()


async def start_redis_subscriber():
    """Start the Redis subscriber to listen for key expiration events."""
    try:
        await redis_subscriber.listen()
    except Exception as e:
        logger.error(f"Error starting Redis subscriber: {str(e)}")
