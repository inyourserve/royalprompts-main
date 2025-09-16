from fastapi import APIRouter, Depends

from app.utils.redis_manager import get_redis_manager, RedisManager

router = APIRouter()


@router.get("/test-redis")
async def test_redis(redis_manager: RedisManager = Depends(get_redis_manager)):
    await redis_manager.set("test_key", "Hello, Redis!")
    value = await redis_manager.get("test_key")
    return {"redis_value": value}


@router.post("/store-json")
async def store_json(
    data: dict, redis_manager: RedisManager = Depends(get_redis_manager)
):
    await redis_manager.set_json("json_key", data, expiration=3600)  # expires in 1 hour
    return {"message": "Data stored in Redis"}


@router.get("/get-json")
async def get_json(redis_manager: RedisManager = Depends(get_redis_manager)):
    data = await redis_manager.get_json("json_key")
    return {"data": data}
