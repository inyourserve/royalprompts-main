from bson import ObjectId

from app.db.models.database import motor_db

DEFAULT_REVIEW = {
    "review_done": False,
    "review_id": None,
    "rating": 0,
    "review": "Not rated yet",
    "reviewed_at": None,
}


async def fetch_reviews_for_job(job_document: dict) -> dict:
    """Fetch and structure seeker and provider reviews for a job.

    Args:
        job_document (dict): The job document containing job and review data.

    Returns:
        dict: Formatted seeker_review and provider_review objects.
    """

    async def fetch_review(review_id: ObjectId) -> dict:
        """Fetch and format a single review."""
        if not review_id or not isinstance(review_id, ObjectId):
            return DEFAULT_REVIEW
        review = await motor_db.reviews.find_one({"_id": review_id})
        if not review:
            return DEFAULT_REVIEW
        return {
            "review_done": True,
            "review_id": str(review["_id"]),
            "rating": review.get("rating", 0),
            "review": review.get("review", "Not rated yet"),
            "reviewed_at": review.get("created_at"),
        }

    # Process seeker review
    seeker_review_info = job_document.get("seeker_review", {})
    seeker_review_done = seeker_review_info.get("seeker_review_done", False)
    seeker_review_id = seeker_review_info.get("seeker_review_id")
    if seeker_review_done and seeker_review_id:
        seeker_review = await fetch_review(seeker_review_id)
    else:
        seeker_review = DEFAULT_REVIEW
        seeker_review["review_done"] = (
            seeker_review_done  # Update based on job document
        )
        seeker_review["review_id"] = str(seeker_review_id) if seeker_review_id else None

    # Process provider review
    provider_review_info = job_document.get("provider_review", {})
    provider_review_done = provider_review_info.get("provider_review_done", False)
    provider_review_id = provider_review_info.get("provider_review_id")
    if provider_review_done and provider_review_id:
        provider_review = await fetch_review(provider_review_id)
    else:
        provider_review = DEFAULT_REVIEW
        provider_review["review_done"] = (
            provider_review_done  # Update based on job document
        )
        provider_review["review_id"] = (
            str(provider_review_id) if provider_review_id else None
        )

    return {
        "seeker_review": seeker_review,
        "provider_review": provider_review,
    }
