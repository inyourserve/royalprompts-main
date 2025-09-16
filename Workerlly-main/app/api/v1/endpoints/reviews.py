from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import PyMongoError

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.review import ReviewCreate, ReviewResponse, UserReviewStats
from app.db.models.database import motor_db
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()


# Define our validation handler function that will be exported and used in main.py
def get_empty_review_message():
    """Return a user-friendly message for empty review validation errors"""
    return "Review message can't be empty"


@router.post("/reviews", response_model=ReviewResponse)
async def create_review(
        review: ReviewCreate, current_user: dict = Depends(get_current_user)
):
    async with await motor_db.client.start_session() as session:
        async with session.start_transaction():
            try:
                # Fetch the job
                job = await motor_db.jobs.find_one({"_id": review.job_id})
                if not job:
                    raise HTTPException(status_code=404, detail="Job not found")

                if job["status"] != "completed":
                    raise HTTPException(
                        status_code=400,
                        detail="Reviews can only be submitted for completed jobs",
                    )

                # Determine reviewer role and reviewee ID
                if str(job["user_id"]) == current_user["user_id"]:
                    reviewer_role = "provider"
                    reviewee_id = str(job["assigned_to"])
                    reviewee_role = "seeker"
                elif str(job["assigned_to"]) == current_user["user_id"]:
                    reviewer_role = "seeker"
                    reviewee_id = str(job["user_id"])
                    reviewee_role = "provider"
                else:
                    raise HTTPException(
                        status_code=403,
                        detail="You are not authorized to review this job",
                    )

                # Check for existing review
                existing_review = await motor_db.reviews.find_one(
                    {
                        "job_id": review.job_id,
                        "reviewer_id": ObjectId(current_user["user_id"]),
                    },
                    session=session,
                )
                if existing_review:
                    raise HTTPException(
                        status_code=400,
                        detail="You have already submitted a review for this job",
                    )

                # Create the review
                review_data = {
                    "job_id": review.job_id,
                    "reviewer_id": ObjectId(current_user["user_id"]),
                    "reviewee_id": ObjectId(reviewee_id),
                    "reviewer_role": reviewer_role,
                    "rating": review.rating,
                    "review": review.review,
                    "created_at": datetime.utcnow(),
                }
                result = await motor_db.reviews.insert_one(review_data, session=session)
                review_data["_id"] = result.inserted_id

                # Update user stats for the reviewee
                await motor_db.user_stats.update_one(
                    {"user_id": ObjectId(reviewee_id)},
                    {
                        "$inc": {
                            f"{reviewee_role}_stats.total_reviews": 1,
                            f"{reviewee_role}_stats.sum_ratings": review.rating,
                        }
                    },
                    session=session,
                )

                # Recalculate average rating
                updated_stats_doc = await motor_db.user_stats.find_one(
                    {"user_id": ObjectId(reviewee_id)}, session=session
                )
                updated_stats = extract_user_stats(updated_stats_doc)
                reviewee_stats = updated_stats.get(f"{reviewee_role}_stats", {})
                new_avg = (
                    reviewee_stats.get("sum_ratings", 0)
                    / reviewee_stats.get("total_reviews", 1)
                    if reviewee_stats.get("total_reviews", 0) > 0
                    else 0
                )

                await motor_db.user_stats.update_one(
                    {"user_id": ObjectId(reviewee_id)},
                    {"$set": {f"{reviewee_role}_stats.avg_rating": new_avg}},
                    session=session,
                )

                # Update the job collection with review information
                review_info = {
                    f"{reviewer_role}_review": {
                        f"{reviewer_role}_review_done": True,
                        f"{reviewer_role}_review_id": result.inserted_id,
                        "reviewed_at": datetime.utcnow(),
                    }
                }
                await motor_db.jobs.update_one(
                    {"_id": review.job_id}, {"$set": review_info}, session=session
                )

                # Remove reviewee_id before returning the response
                del review_data["reviewee_id"]
                return ReviewResponse(**review_data)

            except PyMongoError as e:
                # If any database operation fails, the transaction will automatically roll back
                raise HTTPException(
                    status_code=500,
                    detail=f"An error occurred while processing the review: {str(e)}",
                )


@router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
async def get_user_reviews(
        user_id: str,
        role: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
):
    query = {"reviewer_id": ObjectId(user_id)}
    if role:
        if role not in ["provider", "seeker"]:
            raise HTTPException(status_code=400, detail="Invalid role specified")
        query["reviewer_role"] = role

    reviews = await motor_db.reviews.find(query).to_list(length=None)
    return [
        ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
        for review in reviews
    ]


@router.get("/reviews/job/{job_id}", response_model=List[ReviewResponse])
async def get_job_reviews(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    reviews = await motor_db.reviews.find({"job_id": ObjectId(job_id)}).to_list(
        length=None
    )
    return [
        ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
        for review in reviews
    ]


@router.get("/reviews/stats/{user_id}", response_model=UserReviewStats)
async def get_user_review_stats(
        user_id: str, current_user: dict = Depends(get_current_user)
):
    user_stats_doc = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
    if not user_stats_doc:
        raise HTTPException(status_code=404, detail="User stats not found")

    user_stats = extract_user_stats(user_stats_doc)
    provider_stats = user_stats.get("provider_stats", {})
    seeker_stats = user_stats.get("seeker_stats", {})

    return UserReviewStats(
        total_reviews_as_provider=provider_stats.get("total_reviews", 0),
        avg_rating_as_provider=provider_stats.get("avg_rating", 0),
        total_reviews_as_seeker=seeker_stats.get("total_reviews", 0),
        avg_rating_as_seeker=seeker_stats.get("avg_rating", 0),
    )

# from datetime import datetime
# from typing import Optional, List
#
# from bson import ObjectId
# from fastapi import APIRouter, HTTPException, Depends
# from fastapi.exceptions import RequestValidationError
# from pymongo.errors import PyMongoError
#
# from app.api.v1.endpoints.users import get_current_user
# from app.api.v1.schemas.review import ReviewCreate, ReviewResponse, UserReviewStats
# from app.db.models.database import motor_db
# from app.utils.exception_handler import create_validation_exception_handler
# from app.utils.user_stats_extractor import extract_user_stats
#
# router = APIRouter()
#
# # Register the custom validation exception handler
# validation_handler = create_validation_exception_handler()
# router.add_exception_handler(RequestValidationError, validation_handler)
#
#
# @router.post("/reviews", response_model=ReviewResponse)
# async def create_review(
#         review: ReviewCreate, current_user: dict = Depends(get_current_user)
# ):
#     async with await motor_db.client.start_session() as session:
#         async with session.start_transaction():
#             try:
#                 # Fetch the job
#                 job = await motor_db.jobs.find_one({"_id": review.job_id})
#                 if not job:
#                     raise HTTPException(status_code=404, detail="Job not found")
#
#                 if job["status"] != "completed":
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Reviews can only be submitted for completed jobs",
#                     )
#
#                 # Determine reviewer role and reviewee ID
#                 if str(job["user_id"]) == current_user["user_id"]:
#                     reviewer_role = "provider"
#                     reviewee_id = str(job["assigned_to"])
#                     reviewee_role = "seeker"
#                 elif str(job["assigned_to"]) == current_user["user_id"]:
#                     reviewer_role = "seeker"
#                     reviewee_id = str(job["user_id"])
#                     reviewee_role = "provider"
#                 else:
#                     raise HTTPException(
#                         status_code=403,
#                         detail="You are not authorized to review this job",
#                     )
#
#                 # Check for existing review
#                 existing_review = await motor_db.reviews.find_one(
#                     {
#                         "job_id": review.job_id,
#                         "reviewer_id": ObjectId(current_user["user_id"]),
#                     },
#                     session=session,
#                 )
#                 if existing_review:
#                     raise HTTPException(
#                         status_code=400,
#                         detail="You have already submitted a review for this job",
#                     )
#
#                 # Create the review
#                 review_data = {
#                     "job_id": review.job_id,
#                     "reviewer_id": ObjectId(current_user["user_id"]),
#                     "reviewee_id": ObjectId(reviewee_id),
#                     "reviewer_role": reviewer_role,
#                     "rating": review.rating,
#                     "review": review.review,
#                     "created_at": datetime.utcnow(),
#                 }
#                 result = await motor_db.reviews.insert_one(review_data, session=session)
#                 review_data["_id"] = result.inserted_id
#
#                 # Update user stats for the reviewee
#                 await motor_db.user_stats.update_one(
#                     {"user_id": ObjectId(reviewee_id)},
#                     {
#                         "$inc": {
#                             f"{reviewee_role}_stats.total_reviews": 1,
#                             f"{reviewee_role}_stats.sum_ratings": review.rating,
#                         }
#                     },
#                     session=session,
#                 )
#
#                 # Recalculate average rating
#                 updated_stats_doc = await motor_db.user_stats.find_one(
#                     {"user_id": ObjectId(reviewee_id)}, session=session
#                 )
#                 updated_stats = extract_user_stats(updated_stats_doc)
#                 reviewee_stats = updated_stats.get(f"{reviewee_role}_stats", {})
#                 new_avg = (
#                     reviewee_stats.get("sum_ratings", 0)
#                     / reviewee_stats.get("total_reviews", 1)
#                     if reviewee_stats.get("total_reviews", 0) > 0
#                     else 0
#                 )
#
#                 await motor_db.user_stats.update_one(
#                     {"user_id": ObjectId(reviewee_id)},
#                     {"$set": {f"{reviewee_role}_stats.avg_rating": new_avg}},
#                     session=session,
#                 )
#
#                 # Update the job collection with review information
#                 review_info = {
#                     f"{reviewer_role}_review": {
#                         f"{reviewer_role}_review_done": True,
#                         f"{reviewer_role}_review_id": result.inserted_id,
#                         "reviewed_at": datetime.utcnow(),
#                     }
#                 }
#                 await motor_db.jobs.update_one(
#                     {"_id": review.job_id}, {"$set": review_info}, session=session
#                 )
#
#                 # Remove reviewee_id before returning the response
#                 del review_data["reviewee_id"]
#                 return ReviewResponse(**review_data)
#
#             except PyMongoError as e:
#                 # If any database operation fails, the transaction will automatically roll back
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"An error occurred while processing the review: {str(e)}",
#                 )
#
#
# @router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
# async def get_user_reviews(
#         user_id: str,
#         role: Optional[str] = None,
#         current_user: dict = Depends(get_current_user),
# ):
#     query = {"reviewer_id": ObjectId(user_id)}
#     if role:
#         if role not in ["provider", "seeker"]:
#             raise HTTPException(status_code=400, detail="Invalid role specified")
#         query["reviewer_role"] = role
#
#     reviews = await motor_db.reviews.find(query).to_list(length=None)
#     return [
#         ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
#         for review in reviews
#     ]
#
#
# @router.get("/reviews/job/{job_id}", response_model=List[ReviewResponse])
# async def get_job_reviews(job_id: str, current_user: dict = Depends(get_current_user)):
#     job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#
#     reviews = await motor_db.reviews.find({"job_id": ObjectId(job_id)}).to_list(
#         length=None
#     )
#     return [
#         ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
#         for review in reviews
#     ]
#
#
# @router.get("/reviews/stats/{user_id}", response_model=UserReviewStats)
# async def get_user_review_stats(
#         user_id: str, current_user: dict = Depends(get_current_user)
# ):
#     user_stats_doc = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
#     if not user_stats_doc:
#         raise HTTPException(status_code=404, detail="User stats not found")
#
#     user_stats = extract_user_stats(user_stats_doc)
#     provider_stats = user_stats.get("provider_stats", {})
#     seeker_stats = user_stats.get("seeker_stats", {})
#
#     return UserReviewStats(
#         total_reviews_as_provider=provider_stats.get("total_reviews", 0),
#         avg_rating_as_provider=provider_stats.get("avg_rating", 0),
#         total_reviews_as_seeker=seeker_stats.get("total_reviews", 0),
#         avg_rating_as_seeker=seeker_stats.get("avg_rating", 0),
#     )
#
# # from datetime import datetime
# # from typing import Optional, List
# #
# # from bson import ObjectId
# # from fastapi import APIRouter, HTTPException, Depends
# # from pymongo.errors import PyMongoError
# #
# # from app.api.v1.endpoints.users import get_current_user
# # from app.api.v1.schemas.review import ReviewCreate, ReviewResponse, UserReviewStats
# # from app.db.models.database import motor_db
# # from app.utils.user_stats_extractor import extract_user_stats
# #
# # router = APIRouter()
# #
# #
# # @router.post("/reviews", response_model=ReviewResponse)
# # async def create_review(
# #     review: ReviewCreate, current_user: dict = Depends(get_current_user)
# # ):
# #     async with await motor_db.client.start_session() as session:
# #         async with session.start_transaction():
# #             try:
# #                 # Fetch the job
# #                 job = await motor_db.jobs.find_one({"_id": review.job_id})
# #                 if not job:
# #                     raise HTTPException(status_code=404, detail="Job not found")
# #
# #                 if job["status"] != "completed":
# #                     raise HTTPException(
# #                         status_code=400,
# #                         detail="Reviews can only be submitted for completed jobs",
# #                     )
# #
# #                 # Determine reviewer role and reviewee ID
# #                 if str(job["user_id"]) == current_user["user_id"]:
# #                     reviewer_role = "provider"
# #                     reviewee_id = str(job["assigned_to"])
# #                     reviewee_role = "seeker"
# #                 elif str(job["assigned_to"]) == current_user["user_id"]:
# #                     reviewer_role = "seeker"
# #                     reviewee_id = str(job["user_id"])
# #                     reviewee_role = "provider"
# #                 else:
# #                     raise HTTPException(
# #                         status_code=403,
# #                         detail="You are not authorized to review this job",
# #                     )
# #
# #                 # Check for existing review
# #                 existing_review = await motor_db.reviews.find_one(
# #                     {
# #                         "job_id": review.job_id,
# #                         "reviewer_id": ObjectId(current_user["user_id"]),
# #                     },
# #                     session=session,
# #                 )
# #                 if existing_review:
# #                     raise HTTPException(
# #                         status_code=400,
# #                         detail="You have already submitted a review for this job",
# #                     )
# #
# #                 # Create the review
# #                 review_data = {
# #                     "job_id": review.job_id,
# #                     "reviewer_id": ObjectId(current_user["user_id"]),
# #                     "reviewee_id": ObjectId(reviewee_id),
# #                     "reviewer_role": reviewer_role,
# #                     "rating": review.rating,
# #                     "review": review.review,
# #                     "created_at": datetime.utcnow(),
# #                 }
# #                 result = await motor_db.reviews.insert_one(review_data, session=session)
# #                 review_data["_id"] = result.inserted_id
# #
# #                 # Update user stats for the reviewee
# #                 await motor_db.user_stats.update_one(
# #                     {"user_id": ObjectId(reviewee_id)},
# #                     {
# #                         "$inc": {
# #                             f"{reviewee_role}_stats.total_reviews": 1,
# #                             f"{reviewee_role}_stats.sum_ratings": review.rating,
# #                         }
# #                     },
# #                     session=session,
# #                 )
# #
# #                 # Recalculate average rating
# #                 updated_stats_doc = await motor_db.user_stats.find_one(
# #                     {"user_id": ObjectId(reviewee_id)}, session=session
# #                 )
# #                 updated_stats = extract_user_stats(updated_stats_doc)
# #                 reviewee_stats = updated_stats.get(f"{reviewee_role}_stats", {})
# #                 new_avg = (
# #                     reviewee_stats.get("sum_ratings", 0)
# #                     / reviewee_stats.get("total_reviews", 1)
# #                     if reviewee_stats.get("total_reviews", 0) > 0
# #                     else 0
# #                 )
# #
# #                 await motor_db.user_stats.update_one(
# #                     {"user_id": ObjectId(reviewee_id)},
# #                     {"$set": {f"{reviewee_role}_stats.avg_rating": new_avg}},
# #                     session=session,
# #                 )
# #
# #                 # Update the job collection with review information
# #                 review_info = {
# #                     f"{reviewer_role}_review": {
# #                         f"{reviewer_role}_review_done": True,
# #                         f"{reviewer_role}_review_id": result.inserted_id,
# #                         "reviewed_at": datetime.utcnow(),
# #                     }
# #                 }
# #                 await motor_db.jobs.update_one(
# #                     {"_id": review.job_id}, {"$set": review_info}, session=session
# #                 )
# #
# #                 # Remove reviewee_id before returning the response
# #                 del review_data["reviewee_id"]
# #                 return ReviewResponse(**review_data)
# #
# #             except PyMongoError as e:
# #                 # If any database operation fails, the transaction will automatically roll back
# #                 raise HTTPException(
# #                     status_code=500,
# #                     detail=f"An error occurred while processing the review: {str(e)}",
# #                 )
# #
# #
# # @router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
# # async def get_user_reviews(
# #     user_id: str,
# #     role: Optional[str] = None,
# #     current_user: dict = Depends(get_current_user),
# # ):
# #     query = {"reviewer_id": ObjectId(user_id)}
# #     if role:
# #         if role not in ["provider", "seeker"]:
# #             raise HTTPException(status_code=400, detail="Invalid role specified")
# #         query["reviewer_role"] = role
# #
# #     reviews = await motor_db.reviews.find(query).to_list(length=None)
# #     return [
# #         ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
# #         for review in reviews
# #     ]
# #
# #
# # @router.get("/reviews/job/{job_id}", response_model=List[ReviewResponse])
# # async def get_job_reviews(job_id: str, current_user: dict = Depends(get_current_user)):
# #     job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
# #     if not job:
# #         raise HTTPException(status_code=404, detail="Job not found")
# #
# #     reviews = await motor_db.reviews.find({"job_id": ObjectId(job_id)}).to_list(
# #         length=None
# #     )
# #     return [
# #         ReviewResponse(**{k: v for k, v in review.items() if k != "reviewee_id"})
# #         for review in reviews
# #     ]
# #
# #
# # @router.get("/reviews/stats/{user_id}", response_model=UserReviewStats)
# # async def get_user_review_stats(
# #     user_id: str, current_user: dict = Depends(get_current_user)
# # ):
# #     user_stats_doc = await motor_db.user_stats.find_one({"user_id": ObjectId(user_id)})
# #     if not user_stats_doc:
# #         raise HTTPException(status_code=404, detail="User stats not found")
# #
# #     user_stats = extract_user_stats(user_stats_doc)
# #     provider_stats = user_stats.get("provider_stats", {})
# #     seeker_stats = user_stats.get("seeker_stats", {})
# #
# #     return UserReviewStats(
# #         total_reviews_as_provider=provider_stats.get("total_reviews", 0),
# #         avg_rating_as_provider=provider_stats.get("avg_rating", 0),
# #         total_reviews_as_seeker=seeker_stats.get("total_reviews", 0),
# #         avg_rating_as_seeker=seeker_stats.get("avg_rating", 0),
# #     )
