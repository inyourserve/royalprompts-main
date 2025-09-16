import logging
from datetime import datetime
from random import randint
from typing import Dict, Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.bid import (
    BidCreate,
    BidResponse,
    BidListResponse,
    bid_helper,
    BidUpdate,
)
from app.db.models.database import motor_db
from app.services.redis_service import get_redis_service
from app.utils.distance_calculator import calculate_distance, estimate_time
from app.utils.platform_fee_calculator import get_fee_calculator
from app.utils.redis_manager import RedisManager, get_redis_manager
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats
from app.utils.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)

fee_calculator = get_fee_calculator()


async def get_user_stats(user_id: ObjectId):
    return await motor_db.user_stats.find_one({"user_id": user_id})


async def get_job(job_id: ObjectId):
    return await motor_db.jobs.find_one({"_id": job_id})


async def update_wallet_and_create_transaction(
    user_id: ObjectId,
    amount: float,
    # transaction_type: str,
    description: str,
    job_id: ObjectId,
    session,
    fee_breakdown: dict = None,
):
    # Update only the seeker's wallet balance
    await motor_db.user_stats.update_one(
        {"user_id": user_id},
        {"$inc": {"seeker_stats.wallet_balance": amount}},
        session=session,
    )

    # Create transaction
    transaction = {
        "user_id": user_id,
        "amount": amount,
        "transaction_type": "debit",
        "description": description,
        "job_id": job_id,
        "fee_breakdown": fee_breakdown,
        "created_at": datetime.utcnow(),
    }
    await motor_db.transactions.insert_one(transaction, session=session)


def get_estimated_time(point1: Dict[str, float], point2: Dict[str, Any]) -> float:
    try:
        distance = calculate_distance(point1, point2)
        return estimate_time(distance)
    except Exception as e:
        logger.error(f"Error calculating estimated time: {e}")
        return 0


@router.post(
    "/bids", response_model=BidResponse, dependencies=[Depends(role_required("seeker"))]
)
async def create_bid(bid: BidCreate, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])

    # Fetch a user document to check online status
    user = await motor_db.users.find_one({"_id": user_id})
    if not user or not user.get("status", False):
        raise HTTPException(
            status_code=400, detail="You are offline. Please go online to place a bid."
        )

    # fee
    fee_breakdown = fee_calculator.calculate_fee(bid.amount)
    total_fee = fee_breakdown.total_fee

    # Fetch user_stats document to check wallet balance

    user_stats_doc = await get_user_stats(user_id)
    user_stats = extract_user_stats(user_stats_doc or {})
    if not user_stats or user_stats["seeker_stats"]["wallet_balance"] < total_fee:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance to place bid. Kindly Recharge",
        )

    job = await get_job(ObjectId(bid.job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check job status
    if job["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="This job has been cancelled.")
    if job["status"] == "ongoing":
        raise HTTPException(
            status_code=400, detail="This job is already assigned to someone else."
        )
    if job["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invalid job status for bidding.")

    # Proceed with bid creation
    bid_data = bid.dict()
    bid_data.update(
        {
            "user_id": user_id,
            "job_id": ObjectId(bid_data["job_id"]),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    result = await motor_db.bids.insert_one(bid_data)
    created_bid = await motor_db.bids.find_one({"_id": result.inserted_id})

    await handle_new_bid(
        {
            "id": str(result.inserted_id),
            "job_id": str(bid.job_id),
            "amount": bid.amount,
            "seeker_id": str(user_id),
        },
        job,
        user_id,
    )

    return BidResponse.from_mongo(created_bid)


@router.get(
    "/bids/job/{job_id}",
    response_model=BidListResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def list_bids_for_job(
    job_id: str, current_user: dict = Depends(get_current_user)
):
    job = await motor_db.jobs.find_one(
        {"_id": ObjectId(job_id), "user_id": ObjectId(current_user["user_id"])}
    )
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or you don't have permission to view these bids",
        )

    pipeline = [
        {"$match": {"job_id": ObjectId(job_id)}},
        {
            "$lookup": {
                "from": "user_stats",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "seeker_info",
            }
        },
        {"$unwind": "$seeker_info"},
        {
            "$project": {
                "_id": 1,
                "job_id": 1,
                "user_id": 1,
                "amount": 1,
                "status": 1,
                "created_at": 1,
                "seeker_info": {
                    "name": "$seeker_info.personal_info.name",
                    "category": "$seeker_info.seeker_stats.category.category_name",
                    "current_location": "$seeker_info.seeker_stats.location",
                },
                "avg_rating": "$seeker_info.seeker_stats.avg_rating",
                "total_ratings": "$seeker_info.seeker_stats.total_reviews",
            }
        },
    ]

    bids = await motor_db.bids.aggregate(pipeline).to_list(None)

    detailed_bids = []
    for bid in bids:
        estimated_time = get_estimated_time(
            bid["seeker_info"]["current_location"], job["address_snapshot"]["location"]
        )

        detailed_bid = {
            "_id": str(bid["_id"]),
            "job_id": str(bid["job_id"]),
            "seeker_id": str(bid["user_id"]),
            "amount": bid.get("amount", 0),
            "status": bid.get("status", "pending"),
            "seeker_info": bid["seeker_info"],
            "star_rating": bid["avg_rating"],
            "total_ratings": bid["total_ratings"],
            "estimated_time": estimated_time,
            "created_at": bid.get("created_at", datetime.utcnow()),
        }
        detailed_bids.append(bid_helper(detailed_bid))

    return BidListResponse(bids=detailed_bids, total=len(detailed_bids))


async def generate_otp():
    return randint(1000, 9999)


@router.patch(
    "/bids/{bid_id}",
    response_model=BidResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def update_bid_status(
    bid_id: str,
    bid_update: BidUpdate,
    current_user: dict = Depends(get_current_user),
    redis_manager: RedisManager = Depends(get_redis_manager),
):
    logger.info(f"Updating bid status for bid_id: {bid_id}")

    async with await motor_db.client.start_session() as session:
        async with session.start_transaction():
            try:
                bid_and_job = await motor_db.bids.aggregate(
                    [
                        {"$match": {"_id": ObjectId(bid_id)}},
                        {
                            "$lookup": {
                                "from": "jobs",
                                "localField": "job_id",
                                "foreignField": "_id",
                                "as": "job",
                            }
                        },
                        {"$unwind": "$job"},
                        {"$limit": 1},
                    ],
                    session=session,
                ).to_list(1)

                if not bid_and_job:
                    raise HTTPException(status_code=404, detail="Bid not found")

                bid = bid_and_job[0]
                job = bid["job"]

                if str(job["user_id"]) != current_user["user_id"]:
                    raise HTTPException(
                        status_code=403,
                        detail="You don't have permission to update this bid",
                    )

                if job.get("status") == "ongoing" and job.get("assigned_to"):
                    raise HTTPException(
                        status_code=400,
                        detail="This job is already assigned",
                    )
                # Add this before processing bid acceptance
                seeker_stats = await motor_db.user_stats.find_one(
                    {"user_id": bid["user_id"]}, session=session
                )
                if (
                    seeker_stats.get("seeker_stats", {})
                    .get("user_status", {})
                    .get("current_status")
                    == "occupied"
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Seeker is already occupied with another job",
                    )

                update_data = bid_update.dict(exclude_unset=True)
                update_data["updated_at"] = datetime.utcnow()

                if update_data.get("status") == "accepted":

                    otp = await generate_otp()
                    logger.info(f"Generated OTP: {otp} for job: {bid['job_id']}")

                    seeker_stats_doc = await motor_db.user_stats.find_one(
                        {"user_id": bid["user_id"]}, session=session
                    )
                    seeker_stats = extract_user_stats(seeker_stats_doc or {})
                    estimated_time = get_estimated_time(
                        seeker_stats["seeker_stats"]["location"],
                        job["address_snapshot"]["location"],
                    )

                    job_update = {
                        "current_rate": bid["amount"],
                        "status": "ongoing",
                        "assigned_to": bid["user_id"],
                        "estimated_time": estimated_time,
                        "job_booking_time": datetime.utcnow(),
                        "job_start_otp": {"OTP": otp, "is_verified": False},
                    }

                    # result = await motor_db.jobs.update_one(
                    #     {"_id": job["_id"], "status": {"$ne": "ongoing"}},
                    #     {"$set": job_update},
                    #     session=session,
                    # )

                    result = await motor_db.jobs.update_one(
                        {
                            "_id": job["_id"],
                            "status": "pending",  # Must be pending
                            "assigned_to": None,  # Must not be assigned
                        },
                        {"$set": job_update},
                        session=session,
                    )

                    if result.modified_count == 0:
                        raise HTTPException(
                            status_code=400,
                            detail="Failed to update job. It may already be assigned.",
                        )

                    await motor_db.bids.update_one(
                        {"_id": ObjectId(bid_id)},
                        {"$set": update_data},
                        session=session,
                    )

                    # old bid reject for same job
                    # await motor_db.bids.update_many(
                    #     {"job_id": job["_id"], "_id": {"$ne": ObjectId(bid_id)}},
                    #     {
                    #         "$set": {
                    #             "status": "rejected",
                    #             "updated_at": datetime.utcnow(),
                    #         }
                    #     },
                    #     session=session,
                    # )
                    # reject all bids for the job, reject all bids for the seeker
                    await motor_db.bids.update_many(
                        {
                            "$or": [
                                {"job_id": job["_id"]},  # Reject bids for this job
                                {
                                    "user_id": bid["user_id"],
                                    "status": "pending",
                                },  # Reject seeker's other pending bids
                            ],
                            "_id": {"$ne": ObjectId(bid_id)},
                        },
                        {
                            "$set": {
                                "status": "rejected",
                                "updated_at": datetime.utcnow(),
                            }
                        },
                        session=session,
                    )

                    # Calculate fee for accepting the bid
                    fee_breakdown = fee_calculator.calculate_fee(bid["amount"])
                    total_fee = fee_breakdown.total_fee

                    # Deduct the fee from the seeker's wallet

                    await update_wallet_and_create_transaction(
                        bid["user_id"],
                        -total_fee,
                        "For Job Lead",
                        job["_id"],
                        session,
                        fee_breakdown=fee_breakdown.dict(),
                    )

                    # Update user status to occupy
                await motor_db.user_stats.update_one(
                    {"user_id": bid["user_id"]},
                    {
                        "$set": {
                            "seeker_stats.user_status": {
                                "current_status": "occupied",
                                "current_job_id": job["_id"],
                                "reason": "Ongoing Job",
                                "status_updated_at": datetime.utcnow(),
                            }
                        }
                    },
                    session=session,
                )

                try:
                    seeker_location = seeker_stats["seeker_stats"]["location"]
                    provider_location = job["address_snapshot"]["location"]

                    active_job_location = {
                        "job_id": job["_id"],
                        "seeker_id": bid["user_id"],
                        "provider_id": ObjectId(current_user["user_id"]),
                        "seeker_location": {
                            "type": "Point",
                            "coordinates": [
                                seeker_location["longitude"],
                                seeker_location["latitude"],
                            ],
                        },
                        "provider_location": {
                            "type": "Point",
                            "coordinates": provider_location["coordinates"],
                        },
                        "created_at": datetime.utcnow(),
                        "last_updated": datetime.utcnow(),
                        "status": "active",
                    }

                    await motor_db.active_job_locations.update_one(
                        {"job_id": job["_id"]},
                        {"$set": active_job_location},
                        upsert=True,
                        session=session,
                    )
                except KeyError as e:
                    logger.error(f"Missing location data: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Error creating active job location due to missing data",
                    )

                updated_bid = await motor_db.bids.find_one(
                    {"_id": ObjectId(bid_id)}, session=session
                )
                if not updated_bid:
                    raise HTTPException(
                        status_code=404, detail="Bid not found after update"
                    )

                # Convert ObjectIds to strings
                updated_bid = {
                    **updated_bid,
                    "_id": str(updated_bid["_id"]),
                    "job_id": str(updated_bid["job_id"]),
                    "user_id": str(updated_bid["user_id"]),
                }

                # Handle bid acceptance (WebSocket notifications)
                await handle_bid_acceptance(
                    updated_bid, job, ObjectId(current_user["user_id"])
                )

                # Remove job notification from Redis
                redis_service = get_redis_service(redis_manager)
                await redis_service.remove_job_notification(
                    str(job["_id"]),
                    str(job["category_id"]),
                    str(job["address_snapshot"]["city_id"]),
                )

                logger.info(f"Successfully updated bid: {updated_bid}")
                return BidResponse(**updated_bid)

            except HTTPException as he:
                raise he
            except Exception as e:
                logger.error(f"Error updating bid: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")


async def handle_new_bid(data: Dict[str, Any], job: Dict[str, Any], user_id: ObjectId):
    seeker_stats_doc = await get_user_stats(ObjectId(data["seeker_id"]))
    seeker_stats = extract_user_stats(seeker_stats_doc or {})

    seeker_info = seeker_stats.get("seeker_stats", {})
    personal_info = seeker_stats.get("personal_info", {})

    estimated_time = get_estimated_time(
        seeker_info.get("location", {"latitude": 0, "longitude": 0}),
        job["address_snapshot"]["location"],
    )

    bid_data = {
        "id": data["id"],
        "job_id": data["job_id"],
        "amount": data["amount"],
        "seeker_id": data["seeker_id"],
        "seeker_name": personal_info.get("name", "Unknown"),
        "seeker_profile_image": personal_info.get("profile_image"),
        "seeker_category_name": seeker_info.get("category", {}).get(
            "category_name", "Unknown"
        ),
        "total_reviews": seeker_info.get("total_reviews", 0),
        "average_rating": round(seeker_info.get("avg_rating", 0), 2),
        "hourly_rate": data["amount"],
        "estimated_time": estimated_time,
    }

    await manager.broadcast(
        {
            "type": "new_bid",
            "data": bid_data,
        },
        user_id=str(job["user_id"]),
    )


async def handle_bid_acceptance(
    data: Dict[str, Any], job: Dict[str, Any], provider_id: ObjectId
):
    bid_id = str(data["_id"])
    job_id = str(job["_id"])
    assigned_user_id = str(data["user_id"])

    # Send acceptance notification to assigned seeker
    await manager.broadcast(
        {
            "type": "bid_status_update",
            "data": {
                "bid_id": bid_id,
                "job_id": job_id,
                "status": "accepted",
            },
        },
        category_id=None,
        city_id=None,
        user_id=assigned_user_id,
    )

    # Send remove_job notification to all users in the job's category and city
    await manager.broadcast(
        {
            "type": "remove_job",
            "data": {
                "job_id": job_id,
            },
        },
        category_id=str(job.get("category_id")),
        city_id=str(job.get("address_snapshot", {}).get("city_id")),
        user_id=None,  # Broadcasting to all users in the category and city
    )

    # Send Bid Rejected
    other_bids_with_providers = await motor_db.bids.aggregate(
        [
            {
                "$match": {
                    "user_id": ObjectId(data["user_id"]),
                    "status": "rejected",
                    "_id": {"$ne": ObjectId(data["_id"])},
                }
            },
            {
                "$lookup": {
                    "from": "jobs",
                    "localField": "job_id",
                    "foreignField": "_id",
                    "as": "job",
                }
            },
            {"$unwind": "$job"},
        ]
    ).to_list(None)

    for bid_info in other_bids_with_providers:
        await manager.broadcast(
            {
                "type": "bid_rejected",
                "data": {
                    "bid_id": str(bid_info["_id"]),
                    "job_id": str(bid_info["job_id"]),
                    "seeker_id": str(bid_info["user_id"]),
                },
            },
            user_id=str(bid_info["job"]["user_id"]),
        )

    updated_job = await get_job(ObjectId(job_id))

    job_details = {
        "id": job_id,
        "title": updated_job.get("title"),
        "description": updated_job.get("description"),
        "hourly_rate": updated_job.get("current_rate"),
        "status": updated_job.get("status"),
        "assigned_to": str(updated_job.get("assigned_to")),
    }

    # Send job details to assigned seeker
    await manager.broadcast(
        {
            "type": "job_details",
            "data": job_details,
        },
        category_id=None,
        city_id=None,
        user_id=assigned_user_id,
    )

    logger.info(f"Job acceptance notification sent to user {assigned_user_id}")
    logger.info(f"Remove job notification broadcast for job {job_id}")
