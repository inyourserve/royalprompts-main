import asyncio
import logging

from bson import ObjectId
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from starlette.websockets import WebSocketState

from app.api.v1.endpoints.bids import handle_new_bid, handle_bid_acceptance
from app.api.v1.endpoints.seeker.jobs import get_job_details
from app.api.v1.endpoints.seeker.update_live_location import handle_location_update
from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.services.redis_service import get_redis_service
from app.utils.redis_manager import get_redis_manager, RedisManager
from app.utils.user_stats_extractor import extract_user_stats
from app.utils.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def unified_websocket_endpoint(
    websocket: WebSocket,
    token: str,
    redis_manager: RedisManager = Depends(get_redis_manager),
):
    user_id = None
    try:
        user = await get_current_user(token)
        if not user:
            logger.warning(
                f"Unauthorized WebSocket connection attempt with token: {token[:10]}..."
            )
            await websocket.close(code=4001)
            return

        user_id = str(user["user_id"])
        roles = user.get("roles", [])

        user_stats_doc = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(user_id)}
        )
        if not user_stats_doc:
            logger.warning(f"User stats not found for ID: {user_id}")
            await websocket.close(code=4004)
            return

        user_stats = extract_user_stats(user_stats_doc)
        seeker_stats = user_stats.get("seeker_stats", {})

        category_id = str(seeker_stats.get("category", {}).get("category_id", ""))
        city_id = str(seeker_stats.get("city_id", ""))

        await manager.connect(
            websocket,
            user_id,
            category_ids=[category_id] if category_id else [],
            city_ids=[city_id] if city_id else [],
            roles=roles,
        )

        logger.info(f"WebSocket connected for user {user_id}")

        # Fetch and send recent job notifications for seekers
        if "seeker" in roles and category_id and city_id:
            redis_service = get_redis_service(redis_manager)
            redis_key = f"job_notifications:{category_id}:{city_id}"
            recent_notifications = await redis_service.get_recent_job_notifications(
                redis_key
            )

            for index, notification_data in enumerate(recent_notifications):
                await manager.send_personal_message(notification_data, user_id)
                if (
                    index < len(recent_notifications) - 1
                ):  # Don't delay after the last notification
                    await asyncio.sleep(2)  # 2-second delay between notifications

        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received message from user {user_id}: {data}")

                if data["type"] == "pong":
                    continue  # Ignore pong messages
                elif data["type"] == "get_job_details":
                    await handle_get_job_details(data, user_id)
                elif data["type"] == "new_bid" and "seeker" in roles:
                    await handle_new_bid_message(data, user_id)
                elif data["type"] == "accept_bid" and "provider" in roles:
                    await handle_accept_bid_message(data, user_id)
                elif data["type"] == "get_bids_for_job" and "provider" in roles:
                    await handle_get_bids_for_job(data, user_id)
                elif data["type"] == "start_tracking" and "provider" in roles:
                    await handle_start_tracking(data, user_id)
                elif data["type"] == "stop_tracking" and "provider" in roles:
                    await handle_stop_tracking(data, user_id)
                elif data["type"] == "location_update" and "seeker" in roles:
                    result = await handle_location_update(
                        user_id, data.get("latitude"), data.get("longitude")
                    )
                    await manager.send_personal_message(result, user_id)
                else:
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": f"Unknown message type: {data['type']}",
                        },
                        user_id,
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                logger.error(
                    f"Error processing WebSocket message for user {user_id}: {str(e)}"
                )
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "An error occurred processing your request",
                    },
                    user_id,
                )

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011)
    finally:
        if user_id:
            manager.disconnect(user_id)


# middle of the code


async def handle_get_job_details(data, user_id):
    job_id = data["job_id"]
    job_details = await get_job_details(job_id)
    if job_details:
        await manager.send_personal_message(
            {"type": "job_details", "data": job_details}, user_id
        )
    else:
        await manager.send_personal_message(
            {"type": "error", "message": f"Job details not found for job {job_id}"},
            user_id,
        )


async def handle_new_bid_message(data, user_id):
    job = await motor_db.jobs.find_one({"_id": ObjectId(data["job_id"])})
    await handle_new_bid(data, job, user_id)


async def handle_accept_bid_message(data, user_id):
    job = await motor_db.jobs.find_one({"_id": ObjectId(data["job_id"])})
    await handle_bid_acceptance(data, job, user_id)


async def handle_get_bids_for_job(data, user_id):
    job_id = data["job_id"]
    bids = await get_bids_for_job(job_id, user_id)
    await manager.send_personal_message({"type": "job_bids", "data": bids}, user_id)


async def handle_start_tracking(data, user_id):
    job_id = data.get("job_id")
    if not job_id:
        await manager.send_personal_message(
            {"type": "error", "message": "Job ID is required for tracking"},
            user_id,
        )
        return

    job = await motor_db.jobs.find_one(
        {"_id": ObjectId(job_id), "user_id": ObjectId(user_id)}
    )
    if not job:
        await manager.send_personal_message(
            {
                "type": "error",
                "message": "Job not found or you're not authorized to track this job",
            },
            user_id,
        )
        return

    manager.start_tracking(user_id, job_id)
    await manager.send_personal_message(
        {"type": "tracking_started", "job_id": job_id}, user_id
    )
    logger.info(f"Started tracking for job {job_id} by provider {user_id}")


async def handle_stop_tracking(data, user_id):
    job_id = data.get("job_id")
    if not job_id:
        await manager.send_personal_message(
            {"type": "error", "message": "Job ID is required to stop tracking"},
            user_id,
        )
        return

    manager.stop_tracking(user_id, job_id)
    await manager.send_personal_message(
        {"type": "tracking_stopped", "job_id": job_id}, user_id
    )
    logger.info(f"Stopped tracking for job {job_id} by provider {user_id}")


async def get_bids_for_job(job_id: str, user_id: str):
    job = await motor_db.jobs.find_one(
        {"_id": ObjectId(job_id), "user_id": ObjectId(user_id)}
    )
    if not job:
        return []

    bids_cursor = motor_db.bids.find({"job_id": ObjectId(job_id)})
    bids = await bids_cursor.to_list(length=None)

    detailed_bids = []
    for bid in bids:
        user_stats_doc = await motor_db.user_stats.find_one({"user_id": bid["user_id"]})
        user_stats = extract_user_stats(user_stats_doc or {})
        seeker_stats = user_stats.get("seeker_stats", {})
        personal_info = user_stats.get("personal_info", {})

        detailed_bid = {
            "id": str(bid["_id"]),
            "job_id": str(bid["job_id"]),
            "seeker_id": str(bid["user_id"]),
            "amount": bid.get("amount", 0),
            "status": bid.get("status", "pending"),
            "seeker_name": personal_info.get("name", "Unknown"),
            "seeker_category": seeker_stats.get("category", {}).get(
                "category_name", "Unknown"
            ),
            "star_rating": seeker_stats.get("avg_rating", 0),
            "total_ratings": seeker_stats.get("total_reviews", 0),
            "created_at": (
                bid.get("created_at").isoformat() if bid.get("created_at") else None
            ),
        }
        detailed_bids.append(detailed_bid)

    return detailed_bids
