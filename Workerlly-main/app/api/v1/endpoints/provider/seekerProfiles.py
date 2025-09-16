import asyncio

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.seeker_profile import SeekerProfile, RatingBreakdown
from app.db.models.database import motor_db
from app.utils.roles import role_required
from app.utils.user_stats_extractor import extract_user_stats

router = APIRouter()

DEFAULT_PROFILE_IMAGE = "public/profiles/default.png"


@router.get(
    "/seeker/{seeker_id}/profile",
    response_model=SeekerProfile,
    dependencies=[Depends(role_required("provider, seeker"))],
)
async def get_seeker_profile(
    seeker_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        # Fetch seeker stats and reviews in parallel
        seeker_stats_doc, seeker_reviews = await asyncio.gather(
            motor_db.user_stats.find_one({"user_id": ObjectId(seeker_id)}),
            motor_db.reviews.find(
                {"reviewee_id": ObjectId(seeker_id), "reviewer_role": "provider"}
            )
            .sort("created_at", -1)
            .to_list(None),
        )

        if not seeker_stats_doc:
            raise HTTPException(status_code=404, detail="Seeker not found")

        seeker_stats = extract_user_stats(seeker_stats_doc)
        seeker_info = seeker_stats.get("seeker_stats", {})
        personal_info = seeker_stats.get("personal_info", {})

        # Calculate rating breakdown and collect unique reviewer IDs
        rating_breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        reviewer_ids = set()
        for review in seeker_reviews:
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
                ].get("name", "Unknown Provider")

        # Format reviews
        formatted_reviews = [
            {
                "provider_name": reviewer_names.get(
                    str(review["reviewer_id"]), "Unknown Provider"
                ),
                "date": review["created_at"],
                "feedback": review.get("review", ""),
                "rating": review["rating"],
            }
            for review in seeker_reviews
        ]

        # Construct SeekerProfile response
        return SeekerProfile(
            id=str(seeker_stats_doc["user_id"]),
            name=personal_info.get("name", ""),
            category=seeker_info.get("category", {}).get("category_name", ""),
            profile_picture=personal_info.get("profile_image") or DEFAULT_PROFILE_IMAGE,
            total_works=seeker_info.get("total_jobs_done", 0),
            average_rating=round(seeker_info.get("avg_rating", 0), 2),
            total_ratings=seeker_info.get("total_reviews", 0),
            rating_breakdown=RatingBreakdown(
                five_star=rating_breakdown[5],
                four_star=rating_breakdown[4],
                three_star=rating_breakdown[3],
                two_star=rating_breakdown[2],
                one_star=rating_breakdown[1],
            ),
            reviews=formatted_reviews,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
