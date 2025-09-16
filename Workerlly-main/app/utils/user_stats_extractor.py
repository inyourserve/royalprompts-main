from typing import Dict, Any

from app.utils.nested_dict import get_nested_value


def extract_user_stats(user_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all information from the user_stats document using get_nested_value.

    :param user_stats: The user_stats document
    :return: A dictionary containing all extracted user information
    """

    def safe_str(value):
        return str(value) if value else None

    return {
        "_id": safe_str(get_nested_value(user_stats, ["_id"], "")),
        "user_id": safe_str(get_nested_value(user_stats, ["user_id"], "")),
        "personal_info": {
            "name": get_nested_value(user_stats, ["personal_info", "name"], ""),
            "email": get_nested_value(user_stats, ["personal_info", "email"], ""),
            "gender": get_nested_value(user_stats, ["personal_info", "gender"], ""),
            "dob": get_nested_value(user_stats, ["personal_info", "dob"], None),
            "marital_status": get_nested_value(
                user_stats, ["personal_info", "marital_status"], ""
            ),
            "religion": get_nested_value(user_stats, ["personal_info", "religion"], ""),
            "diet": get_nested_value(user_stats, ["personal_info", "diet"], ""),
            "profile_image": get_nested_value(
                user_stats, ["personal_info", "profile_image"], None
            ),
        },
        "seeker_stats": {
            "wallet_balance": get_nested_value(
                user_stats, ["seeker_stats", "wallet_balance"], 0
            ),
            "city_id": safe_str(
                get_nested_value(user_stats, ["seeker_stats", "city_id"], None)
            ),
            "city_name": get_nested_value(
                user_stats, ["seeker_stats", "city_name"], ""
            ),
            "category": {
                "category_id": safe_str(
                    get_nested_value(
                        user_stats, ["seeker_stats", "category", "category_id"], None
                    )
                ),
                "category_name": get_nested_value(
                    user_stats, ["seeker_stats", "category", "category_name"], ""
                ),
                "sub_categories": get_nested_value(
                    user_stats, ["seeker_stats", "category", "sub_categories"], []
                ),
            },
            "location": {
                "latitude": get_nested_value(
                    user_stats, ["seeker_stats", "location", "latitude"], None
                ),
                "longitude": get_nested_value(
                    user_stats, ["seeker_stats", "location", "longitude"], None
                ),
            },
            "experience": get_nested_value(
                user_stats, ["seeker_stats", "experience"], 0
            ),
            "user_status": {
                "current_job_id": safe_str(
                    get_nested_value(
                        user_stats,
                        ["seeker_stats", "user_status", "current_job_id"],
                        None,
                    )
                ),
                "current_status": get_nested_value(
                    user_stats, ["seeker_stats", "user_status", "current_status"], ""
                ),
                "reason": get_nested_value(
                    user_stats, ["seeker_stats", "user_status", "reason"], ""
                ),
                "status_updated_at": get_nested_value(
                    user_stats,
                    ["seeker_stats", "user_status", "status_updated_at"],
                    None,
                ),
            },
            "total_jobs_done": get_nested_value(
                user_stats, ["seeker_stats", "total_jobs_done"], 0
            ),
            "total_earned": get_nested_value(
                user_stats, ["seeker_stats", "total_earned"], 0
            ),
            "total_hours_worked": get_nested_value(
                user_stats, ["seeker_stats", "total_hours_worked"], 0
            ),
            "total_reviews": get_nested_value(
                user_stats, ["seeker_stats", "total_reviews"], 0
            ),
            "avg_rating": get_nested_value(
                user_stats, ["seeker_stats", "avg_rating"], 0
            ),
            "sum_ratings": get_nested_value(
                user_stats, ["seeker_stats", "sum_ratings"], 0
            ),
        },
        "provider_stats": {
            "city_id": safe_str(
                get_nested_value(user_stats, ["provider_stats", "city_id"], None)
            ),
            "city_name": get_nested_value(
                user_stats, ["provider_stats", "city_name"], ""
            ),
            "total_jobs_posted": get_nested_value(
                user_stats, ["provider_stats", "total_jobs_posted"], 0
            ),
            "total_jobs_completed": get_nested_value(
                user_stats, ["provider_stats", "total_jobs_completed"], 0
            ),
            "total_jobs_cancelled": get_nested_value(
                user_stats, ["provider_stats", "total_jobs_cancelled"], 0
            ),
            "total_spent": get_nested_value(
                user_stats, ["provider_stats", "total_spent"], 0
            ),
            "total_reviews": get_nested_value(
                user_stats, ["provider_stats", "total_reviews"], 0
            ),
            "avg_rating": get_nested_value(
                user_stats, ["provider_stats", "avg_rating"], 0
            ),
            "sum_ratings": get_nested_value(
                user_stats, ["provider_stats", "sum_ratings"], 0
            ),
        },
    }
