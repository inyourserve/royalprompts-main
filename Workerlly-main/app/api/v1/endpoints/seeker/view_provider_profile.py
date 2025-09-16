import asyncio

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.provider_profile import ProviderProfile, RatingBreakdown
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()

DEFAULT_PROFILE_IMAGE = "public/profiles/default.png"


@router.get(
    "/provider/{provider_id}/profile",
    response_model=ProviderProfile,
    dependencies=[Depends(role_required("seeker, provider"))],
)
async def get_provider_profile(
    provider_id: str, current_user: dict = Depends(get_current_user)
):
    # Fetch provider stats and reviews in parallel
    provider_stats_doc, provider_reviews = await asyncio.gather(
        motor_db.user_stats.find_one({"user_id": ObjectId(provider_id)}),
        motor_db.reviews.find(
            {"reviewee_id": ObjectId(provider_id), "reviewer_role": "seeker"}
        )
        .sort("created_at", -1)
        .to_list(None),
    )

    if not provider_stats_doc:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_stats = extract_user_stats(provider_stats_doc)
    provider_info = provider_stats.get("provider_stats", {})
    personal_info = provider_stats.get("personal_info", {})

    # Calculate rating breakdown and collect unique reviewer IDs
    rating_breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    reviewer_ids = set()
    for review in provider_reviews:
        rating = review.get("rating", 0)
        if 1 <= rating <= 5:
            rating_breakdown[rating] += 1
        reviewer_ids.add(review["reviewer_id"])

    # Fetch all reviewer names in one query
    reviewer_names = {}
    if reviewer_ids:
        reviewers_docs = await motor_db.user_stats.find(
            {"user_id": {"$in": list(reviewer_ids)}}
        ).to_list(None)
        for reviewer_doc in reviewers_docs:
            reviewer_stats = extract_user_stats(reviewer_doc)
            reviewer_names[str(reviewer_doc["user_id"])] = reviewer_stats[
                "personal_info"
            ].get("name", "Unknown Seeker")

    # Format reviews
    formatted_reviews = [
        {
            "seeker_name": reviewer_names.get(
                str(review["reviewer_id"]), "Unknown Seeker"
            ),
            "date": review["created_at"],
            "feedback": review.get("review", ""),
            "rating": review["rating"],
        }
        for review in provider_reviews
    ]

    # Construct ProviderProfile response
    return ProviderProfile(
        id=str(provider_stats_doc["user_id"]),
        name=personal_info.get("name", ""),
        profile_picture=personal_info.get("profile_image") or DEFAULT_PROFILE_IMAGE,
        total_works=provider_info.get("total_jobs_completed", 0),
        average_rating=round(provider_info.get("avg_rating", 0), 2),
        total_ratings=provider_info.get("total_reviews", 0),
        total_spent=provider_info.get("total_spent", 0),
        rating_breakdown=RatingBreakdown(
            five_star=rating_breakdown[5],
            four_star=rating_breakdown[4],
            three_star=rating_breakdown[3],
            two_star=rating_breakdown[2],
            one_star=rating_breakdown[1],
        ),
        reviews=formatted_reviews,
    )
