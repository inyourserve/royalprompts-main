import json
import logging
from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_redis_client():
    try:
        client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        raise


class RedisManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    # Add the new keys method
    async def keys(self, pattern: str):
        """
        Get all keys matching pattern
        """
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            raise

    async def set(self, key: str, value: str, expiration: int = None):
        try:
            return await self.redis.set(key, value, ex=expiration)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            raise

    async def get(self, key: str):
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            raise

    async def delete(self, key: str):
        try:
            return await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            raise

    async def exists(self, key: str):
        try:
            return await self.redis.exists(key)
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            raise

    async def increment(self, key: str):
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            raise

    async def decrement(self, key: str):
        try:
            return await self.redis.decr(key)
        except Exception as e:
            logger.error(f"Redis decrement error: {e}")
            raise

    async def set_json(self, key: str, value: dict, expiration: int = None):
        try:
            return await self.redis.set(key, json.dumps(value), ex=expiration)
        except Exception as e:
            logger.error(f"Redis set_json error: {e}")
            raise

    async def get_json(self, key: str):
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get_json error: {e}")
            raise

    async def push_to_list(self, key: str, value: str):
        try:
            return await self.redis.rpush(key, value)
        except Exception as e:
            logger.error(f"Redis push_to_list error: {e}")
            raise

    async def pop_from_list(self, key: str):
        try:
            return await self.redis.lpop(key)
        except Exception as e:
            logger.error(f"Redis pop_from_list error: {e}")
            raise

    async def get_list(self, key: str):
        try:
            return await self.redis.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Redis get_list error: {e}")
            raise

    async def add_to_set(self, key: str, value: str):
        try:
            return await self.redis.sadd(key, value)
        except Exception as e:
            logger.error(f"Redis add_to_set error: {e}")
            raise

    async def remove_from_set(self, key: str, value: str):
        try:
            return await self.redis.srem(key, value)
        except Exception as e:
            logger.error(f"Redis remove_from_set error: {e}")
            raise

    async def get_set_members(self, key: str):
        try:
            return await self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Redis get_set_members error: {e}")
            raise

    async def set_hash(self, key: str, field: str, value: str):
        try:
            return await self.redis.hset(key, field, value)
        except Exception as e:
            logger.error(f"Redis set_hash error: {e}")
            raise

    async def get_hash(self, key: str, field: str):
        try:
            return await self.redis.hget(key, field)
        except Exception as e:
            logger.error(f"Redis get_hash error: {e}")
            raise

    async def get_all_hash(self, key: str):
        try:
            return await self.redis.hgetall(key)
        except Exception as e:
            logger.error(f"Redis get_all_hash error: {e}")
            raise

    async def zadd(self, key: str, mapping: dict):
        try:
            return await self.redis.zadd(key, mapping)
        except Exception as e:
            logger.error(f"Redis zadd error: {e}")
            raise

    async def zrange(
        self,
        key: str,
        start: int,
        end: int,
        desc: bool = False,
        withscores: bool = False,
    ):
        try:
            return await self.redis.zrange(
                key, start, end, desc=desc, withscores=withscores
            )
        except Exception as e:
            logger.error(f"Redis zrange error: {e}")
            raise

    async def expire(self, key: str, seconds: int):
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            raise

    async def zrem(self, key: str, member: str):
        try:
            return await self.redis.zrem(key, member)
        except Exception as e:
            logger.error(f"Redis zrem error: {e}")
            raise


async def get_redis_manager():
    redis_client = get_redis_client()
    try:
        await redis_client.ping()
        return RedisManager(redis_client)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


# import json
# import logging
# from functools import lru_cache
#
# from redis.asyncio import Redis
#
# from app.core.config import settings
#
# logger = logging.getLogger(__name__)
#
#
# @lru_cache()
# def get_redis_client():
#     try:
#         client = Redis(
#             host=settings.REDIS_HOST,
#             port=settings.REDIS_PORT,
#             password=settings.REDIS_PASSWORD,
#             decode_responses=True,
#         )
#         return client
#     except Exception as e:
#         logger.error(f"Failed to create Redis client: {e}")
#         raise
#
#
# class RedisManager:
#     def __init__(self, redis_client: Redis):
#         self.redis = redis_client
#
#     async def set(self, key: str, value: str, expiration: int = None):
#         try:
#             return await self.redis.set(key, value, ex=expiration)
#         except Exception as e:
#             logger.error(f"Redis set error: {e}")
#             raise
#
#     async def get(self, key: str):
#         try:
#             return await self.redis.get(key)
#         except Exception as e:
#             logger.error(f"Redis get error: {e}")
#             raise
#
#     async def delete(self, key: str):
#         try:
#             return await self.redis.delete(key)
#         except Exception as e:
#             logger.error(f"Redis delete error: {e}")
#             raise
#
#     async def exists(self, key: str):
#         try:
#             return await self.redis.exists(key)
#         except Exception as e:
#             logger.error(f"Redis exists error: {e}")
#             raise
#
#     async def increment(self, key: str):
#         try:
#             return await self.redis.incr(key)
#         except Exception as e:
#             logger.error(f"Redis increment error: {e}")
#             raise
#
#     async def decrement(self, key: str):
#         try:
#             return await self.redis.decr(key)
#         except Exception as e:
#             logger.error(f"Redis decrement error: {e}")
#             raise
#
#     async def set_json(self, key: str, value: dict, expiration: int = None):
#         try:
#             return await self.redis.set(key, json.dumps(value), ex=expiration)
#         except Exception as e:
#             logger.error(f"Redis set_json error: {e}")
#             raise
#
#     async def get_json(self, key: str):
#         try:
#             value = await self.redis.get(key)
#             return json.loads(value) if value else None
#         except Exception as e:
#             logger.error(f"Redis get_json error: {e}")
#             raise
#
#     async def push_to_list(self, key: str, value: str):
#         try:
#             return await self.redis.rpush(key, value)
#         except Exception as e:
#             logger.error(f"Redis push_to_list error: {e}")
#             raise
#
#     async def pop_from_list(self, key: str):
#         try:
#             return await self.redis.lpop(key)
#         except Exception as e:
#             logger.error(f"Redis pop_from_list error: {e}")
#             raise
#
#     async def get_list(self, key: str):
#         try:
#             return await self.redis.lrange(key, 0, -1)
#         except Exception as e:
#             logger.error(f"Redis get_list error: {e}")
#             raise
#
#     async def add_to_set(self, key: str, value: str):
#         try:
#             return await self.redis.sadd(key, value)
#         except Exception as e:
#             logger.error(f"Redis add_to_set error: {e}")
#             raise
#
#     async def remove_from_set(self, key: str, value: str):
#         try:
#             return await self.redis.srem(key, value)
#         except Exception as e:
#             logger.error(f"Redis remove_from_set error: {e}")
#             raise
#
#     async def get_set_members(self, key: str):
#         try:
#             return await self.redis.smembers(key)
#         except Exception as e:
#             logger.error(f"Redis get_set_members error: {e}")
#             raise
#
#     async def set_hash(self, key: str, field: str, value: str):
#         try:
#             return await self.redis.hset(key, field, value)
#         except Exception as e:
#             logger.error(f"Redis set_hash error: {e}")
#             raise
#
#     async def get_hash(self, key: str, field: str):
#         try:
#             return await self.redis.hget(key, field)
#         except Exception as e:
#             logger.error(f"Redis get_hash error: {e}")
#             raise
#
#     async def get_all_hash(self, key: str):
#         try:
#             return await self.redis.hgetall(key)
#         except Exception as e:
#             logger.error(f"Redis get_all_hash error: {e}")
#             raise
#
#     async def zadd(self, key: str, mapping: dict):
#         try:
#             return await self.redis.zadd(key, mapping)
#         except Exception as e:
#             logger.error(f"Redis zadd error: {e}")
#             raise
#
#     async def zrange(
#         self,
#         key: str,
#         start: int,
#         end: int,
#         desc: bool = False,
#         withscores: bool = False,
#     ):
#         try:
#             return await self.redis.zrange(
#                 key, start, end, desc=desc, withscores=withscores
#             )
#         except Exception as e:
#             logger.error(f"Redis zrange error: {e}")
#             raise
#
#     async def expire(self, key: str, seconds: int):
#         try:
#             return await self.redis.expire(key, seconds)
#         except Exception as e:
#             logger.error(f"Redis expire error: {e}")
#             raise
#
#     async def zrem(self, key: str, member: str):
#         try:
#             return await self.redis.zrem(key, member)
#         except Exception as e:
#             logger.error(f"Redis zrem error: {e}")
#             raise
#
#
# async def get_redis_manager():
#     redis_client = get_redis_client()
#     try:
#         await redis_client.ping()
#         return RedisManager(redis_client)
#     except Exception as e:
#         logger.error(f"Failed to connect to Redis: {e}")
#         raise
