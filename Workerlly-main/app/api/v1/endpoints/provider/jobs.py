# version 1
# import logging
# from datetime import datetime
# from typing import List, Dict
#
# from bson import ObjectId
# from fastapi import APIRouter, HTTPException, Depends, Query
#
# from app.api.v1.endpoints.users import get_current_user
# from app.api.v1.schemas.jobprovider import (
#     JobCreate,
#     JobResponse,
#     AddressSnapshot,
#     HourlyRateUpdate,
#     CancelJobResponse,
# )
# from app.db.models.database import motor_db
# from app.services.redis_service import get_redis_service
# from app.utils.redis_manager import RedisManager, get_redis_manager
# from app.utils.roles import role_required
# from app.utils.task_id_generator import TaskIDGenerator
# from app.utils.websocket_manager import manager
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
#
#
# @router.post(
#     "/jobs",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
#     user_id = ObjectId(current_user["user_id"])
#
#     address = await motor_db.addresses.find_one({"_id": ObjectId(job.address_id)})
#     if not address:
#         raise HTTPException(status_code=404, detail="Address not found")
#
#     address_snapshot = AddressSnapshot(
#         id=address["_id"],
#         address_line1=address["address_line1"],
#         address_line2=address.get("address_line2"),
#         apartment_number=address.get("apartment_number"),
#         landmark=address.get("landmark"),
#         label=address["label"],
#         address_type=address.get("address_type"),
#         location=address["location"],
#         city_id=address["city_id"],
#         type=address.get("type"),
#     )
#
#     task_id = await TaskIDGenerator.generate_task_id(motor_db)
#
#     job_data = job.model_dump()
#     job_data["user_id"] = user_id
#     job_data["task_id"] = task_id
#     job_data["current_rate"] = job.hourly_rate
#     job_data["status"] = "pending"
#     job_data["address_snapshot"] = address_snapshot.model_dump(by_alias=True)
#     job_data["created_at"] = datetime.utcnow()
#     job_data["updated_at"] = datetime.utcnow()
#     job_data["category_id"] = ObjectId(job_data["category_id"])
#     job_data["sub_category_ids"] = [ObjectId(id) for id in job_data["sub_category_ids"]]
#     job_data["address_id"] = ObjectId(job_data["address_id"])
#     job_data["address_snapshot"]["_id"] = ObjectId(job_data["address_snapshot"]["_id"])
#     job_data["address_snapshot"]["city_id"] = ObjectId(
#         job_data["address_snapshot"]["city_id"]
#     )
#
#     session = await motor_db.client.start_session()
#     try:
#         async with session.start_transaction():
#             # Insert the new job
#             result = await motor_db.jobs.insert_one(job_data, session=session)
#             job_data["_id"] = result.inserted_id
#
#             logger.info(f"New job created: {job_data['_id']}")
#
#             # Update user stats
#             await motor_db.user_stats.update_one(
#                 {"user_id": user_id},
#                 {"$inc": {"provider_stats.total_jobs_posted": 1}},
#                 session=session,
#             )
#
#         # Notify connected seekers
#         await manager.broadcast(
#             {
#                 "type": "new_job",
#                 "data": {
#                     "id": str(result.inserted_id),
#                     "sub_category": await get_sub_category_name(
#                         job_data["sub_category_ids"][0]
#                     ),
#                     "location": f"{job_data['address_snapshot']['label']}, {await get_city_name(job_data['address_snapshot']['city_id'])}",
#                     "hourly_rate": job.hourly_rate,
#                 },
#             },
#             category_id=str(job_data["category_id"]),
#             city_id=str(job_data["address_snapshot"]["city_id"]),
#         )
#
#         # Get RedisManager instance
#         redis_manager = await get_redis_manager()
#         redis_service = get_redis_service(redis_manager)
#
#         # Store job notification in Redis
#         await redis_service.store_job_notification(job_data, str(user_id))
#
#         return JobResponse(**job_data)
#     except Exception as e:
#         logger.error(f"Failed to create job with user stats update: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to create job")
#     finally:
#         await session.end_session()
#
#
# @router.get(
#     "/jobs/{job_id}",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def get_job_by_id(job_id: str, current_user: dict = Depends(get_current_user)):
#     try:
#         job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#         if not job:
#             raise HTTPException(status_code=404, detail="Job not found")
#
#         job["_id"] = str(job["_id"])
#         job["task_id"] = str(job["task_id"])
#         job["user_id"] = str(job["user_id"])
#         job["category_id"] = str(job["category_id"])
#         job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
#         job["address_id"] = str(job["address_id"])
#         job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
#         job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])
#
#         provider = await motor_db.users_stats.find_one(
#             {"_id": ObjectId(job["user_id"])}
#         )
#         if provider:
#             job["provider_name"] = provider.get("name", "Unknown Provider")
#             job["provider_rating"] = provider.get("avg_rating_as_provider", 0)
#
#         job["distance"] = 0  # Replace with actual distance calculation
#
#         return JobResponse(**job)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get(
#     "/jobs/user/{user_id}",
#     response_model=Dict[str, List[JobResponse]],
#     dependencies=[Depends(role_required("provider"))],
# )
# async def list_jobs_by_user_id(user_id: str):
#     try:
#         user_object_id = ObjectId(user_id)
#         all_jobs = await motor_db.jobs.find({"user_id": user_object_id}).to_list(
#             length=None
#         )
#
#         job_status_lists = {
#             "pending": [],
#             "ongoing": [],
#             "completed": [],
#             "cancelled": [],
#         }
#
#         for job in all_jobs:
#             job["_id"] = str(job["_id"])
#             job["user_id"] = str(job["user_id"])
#             job["category_id"] = str(job["category_id"])
#             job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
#             job["address_id"] = str(job["address_id"])
#             job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
#             job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])
#
#             status = job.get(
#                 "status", "pending"
#             )  # Default to 'pending' if status is not set
#             if status in job_status_lists:
#                 job_status_lists[status].append(JobResponse(**job))
#             else:
#                 logger.warning(f"Unknown job status '{status}' for job {job['_id']}")
#
#         return job_status_lists
#
#     except Exception as e:
#         logger.error(f"Error listing jobs for user {user_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
#
#
# @router.patch(
#     "/jobs/update-hourly-rate",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def update_job_hourly_rate(
#         rate_update: HourlyRateUpdate, current_user: dict = Depends(get_current_user)
# ):
#     user_id = ObjectId(current_user["user_id"])
#
#     # Find the job and ensure it belongs to the current user
#     job = await motor_db.jobs.find_one(
#         {"_id": ObjectId(rate_update.job_id), "user_id": user_id}
#     )
#     if not job:
#         raise HTTPException(
#             status_code=404,
#             detail="Job not found or you don't have permission to update it",
#         )
#
#     # Fetch the min and max hourly rates for the job's category and city
#     category_id = job["category_id"]
#     city_id = job["address_snapshot"]["city_id"]
#     rate_limits = await motor_db.rates.find_one(
#         {"category_id": category_id, "city_id": city_id}
#     )
#
#     if not rate_limits:
#         raise HTTPException(
#             status_code=404,
#             detail="Rate limits not found for this job's category and city",
#         )
#
#     min_hourly_rate = rate_limits.get("min_hourly_rate")
#     max_hourly_rate = rate_limits.get("max_hourly_rate")
#
#     # Check if the new rate is within the allowed range
#     if min_hourly_rate and rate_update.new_hourly_rate < min_hourly_rate:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Rate can't be lower than {min_hourly_rate}",
#         )
#
#     if max_hourly_rate and rate_update.new_hourly_rate > max_hourly_rate:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Rate can't be higher than {max_hourly_rate}",
#         )
#
#     current_time = datetime.utcnow()
#     new_rate_entry = {"rate": rate_update.new_hourly_rate, "updated_at": current_time}
#
#     # Update the hourly rate and add to history
#     update_result = await motor_db.jobs.update_one(
#         {"_id": ObjectId(rate_update.job_id)},
#         {
#             "$set": {
#                 "current_rate": rate_update.new_hourly_rate,
#                 "updated_at": current_time,
#             },
#             "$push": {"hourly_rate_history": new_rate_entry},
#         },
#     )
#
#     if update_result.modified_count == 0:
#         raise HTTPException(status_code=400, detail="Failed to update hourly rate")
#
#     # Fetch the updated job
#     updated_job = await motor_db.jobs.find_one({"_id": ObjectId(rate_update.job_id)})
#
#     # Convert ObjectId fields to strings
#     updated_job["_id"] = str(updated_job["_id"])
#     updated_job["user_id"] = str(updated_job["user_id"])
#     updated_job["category_id"] = str(updated_job["category_id"])
#     updated_job["sub_category_ids"] = [
#         str(id) for id in updated_job["sub_category_ids"]
#     ]
#     updated_job["address_id"] = str(updated_job["address_id"])
#     updated_job["address_snapshot"]["_id"] = str(updated_job["address_snapshot"]["_id"])
#     updated_job["address_snapshot"]["city_id"] = str(
#         updated_job["address_snapshot"]["city_id"]
#     )
#
#     # Notify connected seekers about the rate update
#     await manager.broadcast(
#         {
#             "type": "job_rate_update",
#             "data": {
#                 "id": str(rate_update.job_id),
#                 "sub_category": await get_sub_category_name(
#                     ObjectId(updated_job["sub_category_ids"][0])
#                 ),
#                 "location": f"{updated_job['address_snapshot']['label']}, {await get_city_name(ObjectId(updated_job['address_snapshot']['city_id']))}",
#                 "hourly_rate": rate_update.new_hourly_rate,
#             },
#         },
#         category_id=str(updated_job["category_id"]),
#         city_id=str(updated_job["address_snapshot"]["city_id"]),
#     )
#
#     return JobResponse(**updated_job)
#
#
# @router.patch(
#     "/jobs/cancel",
#     response_model=CancelJobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def cancel_job(
#         job_id: str = Query(..., description="ID of the job to cancel"),
#         reason: str = Query(..., description="Reason for cancellation"),
#         current_user: dict = Depends(get_current_user),
#         redis_manager: RedisManager = Depends(get_redis_manager),
# ):
#     user_id = ObjectId(current_user["user_id"])
#
#     session = await motor_db.client.start_session()
#     try:
#         async with session.start_transaction():
#             # Find the job and ensure it belongs to the current user
#             job = await motor_db.jobs.find_one(
#                 {"_id": ObjectId(job_id), "user_id": user_id},
#                 session=session,
#             )
#             if not job:
#                 raise HTTPException(
#                     status_code=404,
#                     detail="Job not found or you don't have permission to update it",
#                 )
#
#             # Check if the job status is pending
#             if job["status"] != "pending":
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Only pending jobs can be cancelled",
#                 )
#
#             # Cancel the job
#             update_result = await motor_db.jobs.update_one(
#                 {"_id": ObjectId(job_id)},
#                 {
#                     "$set": {
#                         "status": "cancelled",
#                         "reason": reason,
#                         "updated_at": datetime.utcnow(),
#                     }
#                 },
#                 session=session,
#             )
#
#             if update_result.modified_count == 0:
#                 raise HTTPException(status_code=400, detail="Failed to cancel job")
#
#             # Update provider stats
#             await motor_db.user_stats.update_one(
#                 {"user_id": user_id},
#                 {"$inc": {"provider_stats.total_jobs_cancelled": 1}},
#                 session=session,
#             )
#             # Send a websocket message for job cancellation
#             await manager.broadcast(
#                 {
#                     "type": "remove_job",
#                     "data": {
#                         "job_id": job_id,
#                     },
#                 },
#                 category_id=str(job.get("category_id")),
#                 city_id=str(job.get("address_snapshot", {}).get("city_id")),
#                 user_id=None,  # Broadcasting to all users in the category and city
#             )
#         # Get RedisManager instance
#         redis_manager = await get_redis_manager()
#         redis_service = get_redis_service(redis_manager)
#         # Remove job notification from Redis
#         await redis_service.remove_job_notification(
#             job_id,
#             str(job["category_id"]),
#             str(job["address_snapshot"]["city_id"]),
#         )
#
#         return CancelJobResponse(message="Job has been cancelled")
#     except Exception as e:
#         logger.error(f"Failed to cancel job with user stats update: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to cancel job")
#     finally:
#         await session.end_session()
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

# version 2
# import logging
# from datetime import datetime
# from typing import List, Dict
#
# from bson import ObjectId
# from fastapi import APIRouter, HTTPException, Depends, Query
#
# from app.api.v1.endpoints.users import get_current_user
# from app.api.v1.schemas.jobprovider import (
#     JobCreate,
#     JobResponse,
#     AddressSnapshot,
#     HourlyRateUpdate,
#     CancelJobResponse,
# )
# from app.db.models.database import motor_db
# from app.services.notification_hub import get_notification_hub  # Import NotificationHub
# from app.services.redis_service import get_redis_service
# from app.utils.redis_manager import RedisManager, get_redis_manager
# from app.utils.roles import role_required
# from app.utils.task_id_generator import TaskIDGenerator
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
#
#
# @router.post(
#     "/jobs",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
#     user_id = ObjectId(current_user["user_id"])
#
#     address = await motor_db.addresses.find_one({"_id": ObjectId(job.address_id)})
#     if not address:
#         raise HTTPException(status_code=404, detail="Address not found")
#
#     address_snapshot = AddressSnapshot(
#         id=address["_id"],
#         address_line1=address["address_line1"],
#         address_line2=address.get("address_line2"),
#         apartment_number=address.get("apartment_number"),
#         landmark=address.get("landmark"),
#         label=address["label"],
#         address_type=address.get("address_type"),
#         location=address["location"],
#         city_id=address["city_id"],
#         type=address.get("type"),
#     )
#
#     task_id = await TaskIDGenerator.generate_task_id(motor_db)
#
#     job_data = job.model_dump()
#     job_data["user_id"] = user_id
#     job_data["task_id"] = task_id
#     job_data["current_rate"] = job.hourly_rate
#     job_data["status"] = "pending"
#     job_data["address_snapshot"] = address_snapshot.model_dump(by_alias=True)
#     job_data["created_at"] = datetime.utcnow()
#     job_data["updated_at"] = datetime.utcnow()
#     job_data["category_id"] = ObjectId(job_data["category_id"])
#     job_data["sub_category_ids"] = [ObjectId(id) for id in job_data["sub_category_ids"]]
#     job_data["address_id"] = ObjectId(job_data["address_id"])
#     job_data["address_snapshot"]["_id"] = ObjectId(job_data["address_snapshot"]["_id"])
#     job_data["address_snapshot"]["city_id"] = ObjectId(
#         job_data["address_snapshot"]["city_id"]
#     )
#
#     session = await motor_db.client.start_session()
#     try:
#         async with session.start_transaction():
#             # Insert the new job
#             result = await motor_db.jobs.insert_one(job_data, session=session)
#             job_data["_id"] = result.inserted_id
#
#             logger.info(f"New job created: {job_data['_id']}")
#
#             # Update user stats
#             await motor_db.user_stats.update_one(
#                 {"user_id": user_id},
#                 {"$inc": {"provider_stats.total_jobs_posted": 1}},
#                 session=session,
#             )
#
#         # Get sub_category name for notification
#         sub_category_name = await get_sub_category_name(job_data["sub_category_ids"][0])
#         city_name = await get_city_name(job_data["address_snapshot"]["city_id"])
#         location = f"{job_data['address_snapshot']['label']}, {city_name}"
#
#         # Send notification using NotificationHub
#         notification_hub = get_notification_hub()
#         await notification_hub.send(
#             event_type="NEW_JOB",
#             data={
#                 "job_id": str(result.inserted_id),
#                 "sub_category": sub_category_name,
#                 "location": location,
#                 "hourly_rate": job.hourly_rate,
#             },
#             context={
#                 "category_id": str(job_data["category_id"]),
#                 "city_id": str(job_data["address_snapshot"]["city_id"]),
#             }
#         )
#
#         # Keep existing Redis functionality
#         redis_manager = await get_redis_manager()
#         redis_service = get_redis_service(redis_manager)
#         await redis_service.store_job_notification(job_data, str(user_id))
#
#         return JobResponse(**job_data)
#
#     except Exception as e:
#         logger.error(f"Failed to create job with user stats update: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to create job")
#     finally:
#         await session.end_session()
#
#
# @router.get(
#     "/jobs/{job_id}",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def get_job_by_id(job_id: str, current_user: dict = Depends(get_current_user)):
#     try:
#         job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#         if not job:
#             raise HTTPException(status_code=404, detail="Job not found")
#
#         job["_id"] = str(job["_id"])
#         job["task_id"] = str(job["task_id"])
#         job["user_id"] = str(job["user_id"])
#         job["category_id"] = str(job["category_id"])
#         job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
#         job["address_id"] = str(job["address_id"])
#         job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
#         job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])
#
#         provider = await motor_db.users_stats.find_one(
#             {"_id": ObjectId(job["user_id"])}
#         )
#         if provider:
#             job["provider_name"] = provider.get("name", "Unknown Provider")
#             job["provider_rating"] = provider.get("avg_rating_as_provider", 0)
#
#         job["distance"] = 0  # Replace with actual distance calculation
#
#         return JobResponse(**job)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get(
#     "/jobs/user/{user_id}",
#     response_model=Dict[str, List[JobResponse]],
#     dependencies=[Depends(role_required("provider"))],
# )
# async def list_jobs_by_user_id(user_id: str):
#     try:
#         user_object_id = ObjectId(user_id)
#         all_jobs = await motor_db.jobs.find({"user_id": user_object_id}).to_list(
#             length=None
#         )
#
#         job_status_lists = {
#             "pending": [],
#             "ongoing": [],
#             "completed": [],
#             "cancelled": [],
#         }
#
#         for job in all_jobs:
#             job["_id"] = str(job["_id"])
#             job["user_id"] = str(job["user_id"])
#             job["category_id"] = str(job["category_id"])
#             job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
#             job["address_id"] = str(job["address_id"])
#             job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
#             job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])
#
#             status = job.get(
#                 "status", "pending"
#             )  # Default to 'pending' if status is not set
#             if status in job_status_lists:
#                 job_status_lists[status].append(JobResponse(**job))
#             else:
#                 logger.warning(f"Unknown job status '{status}' for job {job['_id']}")
#
#         return job_status_lists
#
#     except Exception as e:
#         logger.error(f"Error listing jobs for user {user_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
#
#
# @router.patch(
#     "/jobs/update-hourly-rate",
#     response_model=JobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def update_job_hourly_rate(
#         rate_update: HourlyRateUpdate, current_user: dict = Depends(get_current_user)
# ):
#     user_id = ObjectId(current_user["user_id"])
#
#     # Find the job and ensure it belongs to the current user
#     job = await motor_db.jobs.find_one(
#         {"_id": ObjectId(rate_update.job_id), "user_id": user_id}
#     )
#     if not job:
#         raise HTTPException(
#             status_code=404,
#             detail="Job not found or you don't have permission to update it",
#         )
#
#     # Fetch the min and max hourly rates for the job's category and city
#     category_id = job["category_id"]
#     city_id = job["address_snapshot"]["city_id"]
#     rate_limits = await motor_db.rates.find_one(
#         {"category_id": category_id, "city_id": city_id}
#     )
#
#     if not rate_limits:
#         raise HTTPException(
#             status_code=404,
#             detail="Rate limits not found for this job's category and city",
#         )
#
#     min_hourly_rate = rate_limits.get("min_hourly_rate")
#     max_hourly_rate = rate_limits.get("max_hourly_rate")
#
#     # Check if the new rate is within the allowed range
#     if min_hourly_rate and rate_update.new_hourly_rate < min_hourly_rate:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Rate can't be lower than {min_hourly_rate}",
#         )
#
#     if max_hourly_rate and rate_update.new_hourly_rate > max_hourly_rate:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Rate can't be higher than {max_hourly_rate}",
#         )
#
#     current_time = datetime.utcnow()
#     new_rate_entry = {"rate": rate_update.new_hourly_rate, "updated_at": current_time}
#
#     # Update the hourly rate and add to history
#     update_result = await motor_db.jobs.update_one(
#         {"_id": ObjectId(rate_update.job_id)},
#         {
#             "$set": {
#                 "current_rate": rate_update.new_hourly_rate,
#                 "updated_at": current_time,
#             },
#             "$push": {"hourly_rate_history": new_rate_entry},
#         },
#     )
#
#     if update_result.modified_count == 0:
#         raise HTTPException(status_code=400, detail="Failed to update hourly rate")
#
#     # Fetch the updated job
#     updated_job = await motor_db.jobs.find_one({"_id": ObjectId(rate_update.job_id)})
#
#     # Convert ObjectId fields to strings
#     updated_job["_id"] = str(updated_job["_id"])
#     updated_job["user_id"] = str(updated_job["user_id"])
#     updated_job["category_id"] = str(updated_job["category_id"])
#     updated_job["sub_category_ids"] = [
#         str(id) for id in updated_job["sub_category_ids"]
#     ]
#     updated_job["address_id"] = str(updated_job["address_id"])
#     updated_job["address_snapshot"]["_id"] = str(updated_job["address_snapshot"]["_id"])
#     updated_job["address_snapshot"]["city_id"] = str(
#         updated_job["address_snapshot"]["city_id"]
#     )
#
#     # Get sub_category name for notification
#     sub_category_name = await get_sub_category_name(ObjectId(updated_job["sub_category_ids"][0]))
#     city_name = await get_city_name(ObjectId(updated_job["address_snapshot"]["city_id"]))
#     location = f"{updated_job['address_snapshot']['label']}, {city_name}"
#
#     # Send notification using NotificationHub
#     notification_hub = get_notification_hub()
#     await notification_hub.send(
#         event_type="JOB_RATE_UPDATE",
#         data={
#             "job_id": str(rate_update.job_id),
#             "sub_category": sub_category_name,
#             "location": location,
#             "hourly_rate": rate_update.new_hourly_rate,
#             "previous_rate": job.get("current_rate", 0)
#         },
#         context={
#             "category_id": str(updated_job["category_id"]),
#             "city_id": str(updated_job["address_snapshot"]["city_id"]),
#         }
#     )
#
#     return JobResponse(**updated_job)
#
#
# @router.patch(
#     "/jobs/cancel",
#     response_model=CancelJobResponse,
#     dependencies=[Depends(role_required("provider"))],
# )
# async def cancel_job(
#         job_id: str = Query(..., description="ID of the job to cancel"),
#         reason: str = Query(..., description="Reason for cancellation"),
#         current_user: dict = Depends(get_current_user),
#         redis_manager: RedisManager = Depends(get_redis_manager),
# ):
#     user_id = ObjectId(current_user["user_id"])
#
#     session = await motor_db.client.start_session()
#     try:
#         async with session.start_transaction():
#             # Find the job and ensure it belongs to the current user
#             job = await motor_db.jobs.find_one(
#                 {"_id": ObjectId(job_id), "user_id": user_id},
#                 session=session,
#             )
#             if not job:
#                 raise HTTPException(
#                     status_code=404,
#                     detail="Job not found or you don't have permission to update it",
#                 )
#
#             # Check if the job status is pending
#             if job["status"] != "pending":
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Only pending jobs can be cancelled",
#                 )
#
#             # Cancel the job
#             update_result = await motor_db.jobs.update_one(
#                 {"_id": ObjectId(job_id)},
#                 {
#                     "$set": {
#                         "status": "cancelled",
#                         "reason": reason,
#                         "updated_at": datetime.utcnow(),
#                     }
#                 },
#                 session=session,
#             )
#
#             if update_result.modified_count == 0:
#                 raise HTTPException(status_code=400, detail="Failed to cancel job")
#
#             # Update provider stats
#             await motor_db.user_stats.update_one(
#                 {"user_id": user_id},
#                 {"$inc": {"provider_stats.total_jobs_cancelled": 1}},
#                 session=session,
#             )
#
#         # Get job details for notification
#         sub_category_name = await get_sub_category_name(job["sub_category_ids"][0])
#         city_name = await get_city_name(job["address_snapshot"]["city_id"])
#         location = f"{job['address_snapshot']['label']}, {city_name}"
#
#         # Send notification using NotificationHub
#         notification_hub = get_notification_hub()
#         await notification_hub.send(
#             event_type="JOB_CANCELLED",
#             data={
#                 "job_id": job_id,
#                 "sub_category": sub_category_name,
#                 "location": location,
#                 "reason": reason,
#                 "provider_name": current_user.get("name", "Unknown Provider")
#             },
#             context={
#                 "category_id": str(job["category_id"]),
#                 "city_id": str(job["address_snapshot"]["city_id"]),
#             }
#         )
#
#         # Keep existing Redis functionality
#         redis_manager = await get_redis_manager()
#         redis_service = get_redis_service(redis_manager)
#         await redis_service.remove_job_notification(
#             job_id,
#             str(job["category_id"]),
#             str(job["address_snapshot"]["city_id"]),
#         )
#
#         return CancelJobResponse(message="Job has been cancelled")
#
#     except Exception as e:
#         logger.error(f"Failed to cancel job with user stats update: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to cancel job")
#     finally:
#         await session.end_session()
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

import logging
from datetime import datetime
from typing import List, Dict

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.jobprovider import (
    JobCreate,
    JobResponse,
    AddressSnapshot,
    HourlyRateUpdate,
    CancelJobResponse,
)
from app.db.models.database import motor_db
from app.services.notification_hub import get_notification_hub  # Import NotificationHub
from app.services.redis_service import get_redis_service
from app.utils.redis_manager import RedisManager, get_redis_manager
from app.utils.roles import role_required
from app.utils.task_id_generator import TaskIDGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/jobs",
    response_model=JobResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])

    address = await motor_db.addresses.find_one({"_id": ObjectId(job.address_id)})
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    address_snapshot = AddressSnapshot(
        id=address["_id"],
        address_line1=address["address_line1"],
        address_line2=address.get("address_line2"),
        apartment_number=address.get("apartment_number"),
        landmark=address.get("landmark"),
        label=address["label"],
        address_type=address.get("address_type"),
        location=address["location"],
        city_id=address["city_id"],
        type=address.get("type"),
    )

    task_id = await TaskIDGenerator.generate_task_id(motor_db)

    job_data = job.model_dump()
    job_data["user_id"] = user_id
    job_data["task_id"] = task_id
    job_data["current_rate"] = job.hourly_rate
    job_data["status"] = "pending"
    job_data["address_snapshot"] = address_snapshot.model_dump(by_alias=True)
    job_data["created_at"] = datetime.utcnow()
    job_data["updated_at"] = datetime.utcnow()
    job_data["category_id"] = ObjectId(job_data["category_id"])
    job_data["sub_category_ids"] = [ObjectId(id) for id in job_data["sub_category_ids"]]
    job_data["address_id"] = ObjectId(job_data["address_id"])
    job_data["address_snapshot"]["_id"] = ObjectId(job_data["address_snapshot"]["_id"])
    job_data["address_snapshot"]["city_id"] = ObjectId(
        job_data["address_snapshot"]["city_id"]
    )

    session = await motor_db.client.start_session()
    try:
        async with session.start_transaction():
            # Insert the new job
            result = await motor_db.jobs.insert_one(job_data, session=session)
            job_data["_id"] = result.inserted_id

            logger.info(f"New job created: {job_data['_id']}")

            # Update user stats
            await motor_db.user_stats.update_one(
                {"user_id": user_id},
                {"$inc": {"provider_stats.total_jobs_posted": 1}},
                session=session,
            )

        # Get sub_category name for notification
        sub_category_name = await get_sub_category_name(job_data["sub_category_ids"][0])
        city_name = await get_city_name(job_data["address_snapshot"]["city_id"])
        location = f"{job_data['address_snapshot']['label']}, {city_name}"

        # Send notification using NotificationHub with OLD format
        notification_hub = get_notification_hub()
        await notification_hub.send(
            event_type="new_job",  # OLD: "new_job" not "NEW_JOB"
            data={
                "id": str(result.inserted_id),  # OLD: "id" not "job_id"
                "sub_category": sub_category_name,
                "location": location,
                "hourly_rate": job.hourly_rate,
            },
            context={
                "category_id": str(job_data["category_id"]),
                "city_id": str(job_data["address_snapshot"]["city_id"]),
            }
        )

        # Keep existing Redis functionality
        redis_manager = await get_redis_manager()
        redis_service = get_redis_service(redis_manager)
        await redis_service.store_job_notification(job_data, str(user_id))

        return JobResponse(**job_data)

    except Exception as e:
        logger.error(f"Failed to create job with user stats update: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job")
    finally:
        await session.end_session()


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def get_job_by_id(job_id: str, current_user: dict = Depends(get_current_user)):
    try:
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job["_id"] = str(job["_id"])
        job["task_id"] = str(job["task_id"])
        job["user_id"] = str(job["user_id"])
        job["category_id"] = str(job["category_id"])
        job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
        job["address_id"] = str(job["address_id"])
        job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
        job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])

        provider = await motor_db.users_stats.find_one(
            {"_id": ObjectId(job["user_id"])}
        )
        if provider:
            job["provider_name"] = provider.get("name", "Unknown Provider")
            job["provider_rating"] = provider.get("avg_rating_as_provider", 0)

        job["distance"] = 0  # Replace with actual distance calculation

        return JobResponse(**job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/jobs/user/{user_id}",
    response_model=Dict[str, List[JobResponse]],
    dependencies=[Depends(role_required("provider"))],
)
async def list_jobs_by_user_id(user_id: str):
    try:
        user_object_id = ObjectId(user_id)
        all_jobs = await motor_db.jobs.find({"user_id": user_object_id}).to_list(
            length=None
        )

        job_status_lists = {
            "pending": [],
            "ongoing": [],
            "completed": [],
            "cancelled": [],
        }

        for job in all_jobs:
            job["_id"] = str(job["_id"])
            job["user_id"] = str(job["user_id"])
            job["category_id"] = str(job["category_id"])
            job["sub_category_ids"] = [str(id) for id in job["sub_category_ids"]]
            job["address_id"] = str(job["address_id"])
            job["address_snapshot"]["_id"] = str(job["address_snapshot"]["_id"])
            job["address_snapshot"]["city_id"] = str(job["address_snapshot"]["city_id"])

            status = job.get(
                "status", "pending"
            )  # Default to 'pending' if status is not set
            if status in job_status_lists:
                job_status_lists[status].append(JobResponse(**job))
            else:
                logger.warning(f"Unknown job status '{status}' for job {job['_id']}")

        return job_status_lists

    except Exception as e:
        logger.error(f"Error listing jobs for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.patch(
    "/jobs/update-hourly-rate",
    response_model=JobResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def update_job_hourly_rate(
        rate_update: HourlyRateUpdate, current_user: dict = Depends(get_current_user)
):
    user_id = ObjectId(current_user["user_id"])

    # Find the job and ensure it belongs to the current user
    job = await motor_db.jobs.find_one(
        {"_id": ObjectId(rate_update.job_id), "user_id": user_id}
    )
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or you don't have permission to update it",
        )

    # Fetch the min and max hourly rates for the job's category and city
    category_id = job["category_id"]
    city_id = job["address_snapshot"]["city_id"]
    rate_limits = await motor_db.rates.find_one(
        {"category_id": category_id, "city_id": city_id}
    )

    if not rate_limits:
        raise HTTPException(
            status_code=404,
            detail="Rate limits not found for this job's category and city",
        )

    min_hourly_rate = rate_limits.get("min_hourly_rate")
    max_hourly_rate = rate_limits.get("max_hourly_rate")

    # Check if the new rate is within the allowed range
    if min_hourly_rate and rate_update.new_hourly_rate < min_hourly_rate:
        raise HTTPException(
            status_code=400,
            detail=f"Rate can't be lower than {min_hourly_rate}",
        )

    if max_hourly_rate and rate_update.new_hourly_rate > max_hourly_rate:
        raise HTTPException(
            status_code=400,
            detail=f"Rate can't be higher than {max_hourly_rate}",
        )

    current_time = datetime.utcnow()
    new_rate_entry = {"rate": rate_update.new_hourly_rate, "updated_at": current_time}

    # Update the hourly rate and add to history
    update_result = await motor_db.jobs.update_one(
        {"_id": ObjectId(rate_update.job_id)},
        {
            "$set": {
                "current_rate": rate_update.new_hourly_rate,
                "updated_at": current_time,
            },
            "$push": {"hourly_rate_history": new_rate_entry},
        },
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update hourly rate")

    # Fetch the updated job
    updated_job = await motor_db.jobs.find_one({"_id": ObjectId(rate_update.job_id)})

    # Convert ObjectId fields to strings
    updated_job["_id"] = str(updated_job["_id"])
    updated_job["user_id"] = str(updated_job["user_id"])
    updated_job["category_id"] = str(updated_job["category_id"])
    updated_job["sub_category_ids"] = [
        str(id) for id in updated_job["sub_category_ids"]
    ]
    updated_job["address_id"] = str(updated_job["address_id"])
    updated_job["address_snapshot"]["_id"] = str(updated_job["address_snapshot"]["_id"])
    updated_job["address_snapshot"]["city_id"] = str(
        updated_job["address_snapshot"]["city_id"]
    )

    # Get sub_category name for notification
    sub_category_name = await get_sub_category_name(ObjectId(updated_job["sub_category_ids"][0]))
    city_name = await get_city_name(ObjectId(updated_job["address_snapshot"]["city_id"]))
    location = f"{updated_job['address_snapshot']['label']}, {city_name}"

    # Send notification using NotificationHub with OLD format
    notification_hub = get_notification_hub()
    await notification_hub.send(
        event_type="job_rate_update",  # OLD: "job_rate_update" not "JOB_RATE_UPDATE"
        data={
            "id": str(rate_update.job_id),  # OLD: "id" not "job_id"
            "sub_category": sub_category_name,
            "location": location,
            "hourly_rate": rate_update.new_hourly_rate,
        },
        context={
            "category_id": str(updated_job["category_id"]),
            "city_id": str(updated_job["address_snapshot"]["city_id"]),
        }
    )

    return JobResponse(**updated_job)


@router.patch(
    "/jobs/cancel",
    response_model=CancelJobResponse,
    dependencies=[Depends(role_required("provider"))],
)
async def cancel_job(
        job_id: str = Query(..., description="ID of the job to cancel"),
        reason: str = Query(..., description="Reason for cancellation"),
        current_user: dict = Depends(get_current_user),
        redis_manager: RedisManager = Depends(get_redis_manager),
):
    user_id = ObjectId(current_user["user_id"])

    session = await motor_db.client.start_session()
    try:
        async with session.start_transaction():
            # Find the job and ensure it belongs to the current user
            job = await motor_db.jobs.find_one(
                {"_id": ObjectId(job_id), "user_id": user_id},
                session=session,
            )
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or you don't have permission to update it",
                )

            # Check if the job status is pending
            if job["status"] != "pending":
                raise HTTPException(
                    status_code=400,
                    detail="Only pending jobs can be cancelled",
                )

            # Cancel the job
            update_result = await motor_db.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "cancelled",
                        "reason": reason,
                        "updated_at": datetime.utcnow(),
                    }
                },
                session=session,
            )

            if update_result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Failed to cancel job")

            # Update provider stats
            await motor_db.user_stats.update_one(
                {"user_id": user_id},
                {"$inc": {"provider_stats.total_jobs_cancelled": 1}},
                session=session,
            )

        # Send notification using NotificationHub with OLD format
        notification_hub = get_notification_hub()
        await notification_hub.send(
            event_type="remove_job",  # OLD: "remove_job" not "JOB_CANCELLED"
            data={
                "job_id": job_id,  # OLD: only "job_id" field
            },
            context={
                "category_id": str(job["category_id"]),
                "city_id": str(job["address_snapshot"]["city_id"]),
            }
        )

        # Keep existing Redis functionality
        redis_manager = await get_redis_manager()
        redis_service = get_redis_service(redis_manager)
        await redis_service.remove_job_notification(
            job_id,
            str(job["category_id"]),
            str(job["address_snapshot"]["city_id"]),
        )

        return CancelJobResponse(message="Job has been cancelled")

    except Exception as e:
        logger.error(f"Failed to cancel job with user stats update: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")
    finally:
        await session.end_session()


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
