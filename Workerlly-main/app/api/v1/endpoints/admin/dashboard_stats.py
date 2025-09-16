# admin/dashboard_stats.py

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import PyMongoError

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required
from app.utils.timezone import DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants for module and actions
MODULE = "dashboard"
ACTIONS = {"VIEW": "read"}


@router.get("/dashboard/overview")
async def get_dashboard_overview(
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"]))
):
    """
    Comprehensive admin dashboard overview with all key metrics
    """
    try:
        # Get current date ranges in IST, then convert to UTC for database queries
        now_ist = datetime.now(DEFAULT_TIMEZONE)
        now_utc = now_ist.astimezone(timezone.utc).replace(tzinfo=None)

        # Calculate IST midnight and convert to UTC
        today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_ist.astimezone(timezone.utc).replace(tzinfo=None)

        # Calculate IST month start and convert to UTC
        month_start_ist = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_utc = month_start_ist.astimezone(timezone.utc).replace(tzinfo=None)

        # Week start (Monday)
        week_start_ist = now_ist - timedelta(days=now_ist.weekday())
        week_start_ist = week_start_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start_utc = week_start_ist.astimezone(timezone.utc).replace(tzinfo=None)

        # ===== JOBS OVERVIEW =====
        jobs_overview = {
            "today": await motor_db.jobs.count_documents({
                "created_at": {"$gte": today_start_utc}
            }),
            "this_week": await motor_db.jobs.count_documents({
                "created_at": {"$gte": week_start_utc}
            }),
            "this_month": await motor_db.jobs.count_documents({
                "created_at": {"$gte": month_start_utc}
            }),
            "total": await motor_db.jobs.count_documents({}),
            "status_breakdown": {
                "posted": await motor_db.jobs.count_documents({"status": "posted"}),
                "assigned": await motor_db.jobs.count_documents({"status": "assigned"}),
                "in_progress": await motor_db.jobs.count_documents({"status": "in_progress"}),
                "completed": await motor_db.jobs.count_documents({"status": "completed"}),
                "cancelled": await motor_db.jobs.count_documents({"status": "cancelled"}),
                "disputed": await motor_db.jobs.count_documents({"status": "disputed"})
            },
            "revenue": {
                "today": 0,  # Will be calculated from completed jobs
                "this_month": 0,
                "total": 0
            }
        }

        # Calculate revenue from completed jobs
        revenue_pipeline = [
            {"$match": {"status": "completed", "payment_status.status": "paid"}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "today_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$created_at", today_start_utc]},
                            "$total_amount",
                            0
                        ]
                    }
                },
                "month_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$created_at", month_start_utc]},
                            "$total_amount",
                            0
                        ]
                    }
                }
            }}
        ]

        revenue_result = await motor_db.jobs.aggregate(revenue_pipeline).to_list(1)
        if revenue_result:
            jobs_overview["revenue"]["total"] = revenue_result[0].get("total_revenue", 0)
            jobs_overview["revenue"]["today"] = revenue_result[0].get("today_revenue", 0)
            jobs_overview["revenue"]["this_month"] = revenue_result[0].get("month_revenue", 0)

        # ===== USERS OVERVIEW =====
        users_overview = {
            "new_today": await motor_db.users.count_documents({
                "created_at": {"$gte": today_start_utc}
            }),
            "new_this_week": await motor_db.users.count_documents({
                "created_at": {"$gte": week_start_utc}
            }),
            "new_this_month": await motor_db.users.count_documents({
                "created_at": {"$gte": month_start_utc}
            }),
            "total_users": await motor_db.users.count_documents({}),
            "active_users": await motor_db.users.count_documents({
                "$or": [
                    {"is_user_blocked": {"$exists": False}},
                    {"is_user_blocked": False}
                ]
            }),
            "blocked_users": await motor_db.users.count_documents({
                "is_user_blocked": True
            }),
            "role_breakdown": {
                "providers": await motor_db.users.count_documents({"roles": "provider"}),
                "seekers": await motor_db.users.count_documents({"roles": "seeker"}),
                "both": await motor_db.users.count_documents({
                    "roles": {"$all": ["provider", "seeker"]}
                })
            }
        }

        # ===== CATEGORIES OVERVIEW =====
        categories_overview = {
            "total_categories": await motor_db.categories.count_documents({
                "deleted_at": None
            }),
            "total_subcategories": 0,
            "new_this_month": await motor_db.categories.count_documents({
                "created_at": {"$gte": month_start_utc},
                "deleted_at": None
            }),
            "most_popular": []
        }

        # Count subcategories
        categories_with_subs = await motor_db.categories.find(
            {"deleted_at": None},
            {"sub_categories": 1}
        ).to_list(None)

        total_subcategories = 0
        for cat in categories_with_subs:
            subcats = [sub for sub in cat.get("sub_categories", []) if sub.get("deleted_at") is None]
            total_subcategories += len(subcats)

        categories_overview["total_subcategories"] = total_subcategories

        # Most popular categories by job count
        popular_categories_cursor = motor_db.jobs.aggregate([
            {"$group": {"_id": "$category_id", "job_count": {"$sum": 1}}},
            {"$sort": {"job_count": -1}},
            {"$limit": 5},
            {"$lookup": {
                "from": "categories",
                "localField": "_id",
                "foreignField": "_id",
                "as": "category_info"
            }},
            {"$unwind": "$category_info"},
            {"$project": {
                "name": "$category_info.name",
                "job_count": 1,
                "_id": 0  # Exclude _id to avoid ObjectId serialization issues
            }}
        ])

        popular_categories = await popular_categories_cursor.to_list(5)
        categories_overview["most_popular"] = popular_categories

        # ===== WORKERS/PROVIDERS OVERVIEW =====
        # Get provider stats from user_stats collection
        provider_stats_pipeline = [
            {"$match": {"provider_stats": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "total_providers": {"$sum": 1},
                "avg_rating": {"$avg": "$provider_stats.avg_rating"},
                "total_jobs_completed": {"$sum": "$provider_stats.total_jobs_completed"},
                "active_today": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$provider_stats.last_active", today_start_utc]},
                            1,
                            0
                        ]
                    }
                }
            }}
        ]

        provider_result = await motor_db.user_stats.aggregate(provider_stats_pipeline).to_list(1)

        workers_overview = {
            "total_providers": provider_result[0].get("total_providers", 0) if provider_result else 0,
            "active_today": provider_result[0].get("active_today", 0) if provider_result else 0,
            "avg_rating": round(provider_result[0].get("avg_rating", 0), 2) if provider_result else 0,
            "total_jobs_completed": provider_result[0].get("total_jobs_completed", 0) if provider_result else 0,
            "new_this_month": await motor_db.users.count_documents({
                "roles": "provider",
                "created_at": {"$gte": month_start_utc}
            })
        }

        # ===== CITIES OVERVIEW =====
        cities_overview = {
            "total_cities": await motor_db.cities.count_documents({}),
            "served_cities": await motor_db.cities.count_documents({"is_served": True}),
            "unserved_cities": await motor_db.cities.count_documents({"is_served": False}),
            "top_cities_by_jobs": []
        }

        # Top cities by job count
        top_cities_cursor = motor_db.jobs.aggregate([
            {"$group": {
                "_id": "$address_snapshot.city_id",
                "job_count": {"$sum": 1}
            }},
            {"$sort": {"job_count": -1}},
            {"$limit": 5},
            {"$lookup": {
                "from": "cities",
                "localField": "_id",
                "foreignField": "_id",
                "as": "city_info"
            }},
            {"$unwind": "$city_info"},
            {"$project": {
                "name": "$city_info.name",
                "job_count": 1,
                "_id": 0  # Exclude _id to avoid ObjectId serialization issues
            }}
        ])

        top_cities = await top_cities_cursor.to_list(5)
        cities_overview["top_cities_by_jobs"] = top_cities

        # ===== RECENT ACTIVITY =====
        recent_activity = {
            "recent_jobs": [],
            "recent_users": [],
            "recent_disputes": await motor_db.jobs.count_documents({
                "status": "disputed",
                "updated_at": {"$gte": today_start_utc}
            }),
            "pending_approvals": await motor_db.users.count_documents({
                "status": "pending_verification"
            })
        }

        # Get recent jobs (last 10)
        recent_jobs_cursor = motor_db.jobs.find({}).sort("created_at", -1).limit(10)
        recent_jobs = []
        async for job in recent_jobs_cursor:
            recent_jobs.append({
                "id": str(job["_id"]),  # Convert ObjectId to string
                "task_id": str(job.get("task_id", "")),  # Ensure task_id is string
                "title": job.get("title", "")[:50],
                "status": job.get("status"),
                "created_at": job.get("created_at").isoformat() if job.get("created_at") else None
            })
        recent_activity["recent_jobs"] = recent_jobs

        # Get recent users (last 10)
        recent_users_cursor = motor_db.users.find({}).sort("created_at", -1).limit(10)
        recent_users = []
        async for user in recent_users_cursor:
            user_stats = await motor_db.user_stats.find_one({"user_id": user["_id"]})
            recent_users.append({
                "id": str(user["_id"]),  # Convert ObjectId to string
                "mobile": user.get("mobile"),
                "name": user_stats.get("personal_info", {}).get("name", "N/A") if user_stats else "N/A",
                "roles": user.get("roles", []),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
            })
        recent_activity["recent_users"] = recent_users

        # ===== SYSTEM HEALTH =====
        system_health = {
            "database_status": "healthy",
            "total_collections": 0,
            "data_integrity": {
                "orphaned_jobs": 0,  # Initialize with 0, will calculate safely
                "incomplete_profiles": 0  # Initialize with 0, will calculate safely
            },
            "last_backup": None,  # You can implement this based on your backup strategy
            "server_uptime": now_ist.isoformat()
        }

        # Safely calculate orphaned jobs
        try:
            user_ids = await motor_db.users.distinct("_id")
            orphaned_jobs = await motor_db.jobs.count_documents({
                "user_id": {"$nin": user_ids}
            })
            system_health["data_integrity"]["orphaned_jobs"] = orphaned_jobs
        except Exception as e:
            logger.warning(f"Could not calculate orphaned jobs: {e}")

        # Safely calculate incomplete profiles
        try:
            user_stat_user_ids = await motor_db.user_stats.distinct("user_id")
            incomplete_profiles = await motor_db.users.count_documents({
                "_id": {"$nin": user_stat_user_ids}
            })
            system_health["data_integrity"]["incomplete_profiles"] = incomplete_profiles
        except Exception as e:
            logger.warning(f"Could not calculate incomplete profiles: {e}")

        # ===== RESPONSE =====
        dashboard_data = {
            "overview": {
                "total_revenue": jobs_overview["revenue"]["total"],
                "total_jobs": jobs_overview["total"],
                "total_users": users_overview["total_users"],
                "active_cities": cities_overview["served_cities"]
            },
            "jobs": jobs_overview,
            "users": users_overview,
            "categories": categories_overview,
            "workers": workers_overview,
            "cities": cities_overview,
            "recent_activity": recent_activity,
            "system_health": system_health,
            "generated_at": now_ist.isoformat(),
            "timezone": "Asia/Kolkata"
        }

        return {
            "status": "success",
            "data": dashboard_data
        }

    except PyMongoError as e:
        logger.error(f"Database error in get_dashboard_overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_overview: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/dashboard/stats/quick")
async def get_quick_stats(
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"]))
):
    """
    Quick stats for real-time dashboard updates
    """
    try:
        now_ist = datetime.now(DEFAULT_TIMEZONE)
        today_start_utc = now_ist.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(
            tzinfo=None)

        quick_stats = {
            "jobs_today": await motor_db.jobs.count_documents({
                "created_at": {"$gte": today_start_utc}
            }),
            "pending_jobs": await motor_db.jobs.count_documents({
                "status": "posted"
            }),
            "active_jobs": await motor_db.jobs.count_documents({
                "status": {"$in": ["assigned", "in_progress", "reached"]}
            }),
            "new_users_today": await motor_db.users.count_documents({
                "created_at": {"$gte": today_start_utc}
            }),
            "disputes_today": await motor_db.jobs.count_documents({
                "status": "disputed",
                "updated_at": {"$gte": today_start_utc}
            }),
            "last_updated": now_ist.isoformat()
        }

        return {
            "status": "success",
            "data": quick_stats
        }

    except Exception as e:
        logger.error(f"Error in get_quick_stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quick stats")


@router.get("/dashboard/analytics/{timeframe}")
async def get_analytics_data(
        timeframe: str,
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"]))
):
    """
    Get analytics data for charts and graphs
    timeframe: daily, weekly, monthly
    """
    try:
        now_ist = datetime.now(DEFAULT_TIMEZONE)

        if timeframe == "daily":
            days = 30
            date_format = "%Y-%m-%d"
        elif timeframe == "weekly":
            days = 84  # 12 weeks
            date_format = "%Y-W%U"
        elif timeframe == "monthly":
            days = 365  # 12 months
            date_format = "%Y-%m"
        else:
            raise HTTPException(status_code=400, detail="Invalid timeframe. Use: daily, weekly, monthly")

        start_date_utc = (now_ist - timedelta(days=days)).astimezone(timezone.utc).replace(tzinfo=None)

        # Jobs analytics - Let timezone middleware handle the conversion
        jobs_analytics_cursor = motor_db.jobs.aggregate([
            {"$match": {"created_at": {"$gte": start_date_utc}}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": date_format,
                        "date": "$created_at",
                        "timezone": "Asia/Kolkata"  # Use MongoDB's built-in timezone support
                    }
                },
                "jobs_count": {"$sum": 1},
                "revenue": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status", "completed"]},
                            "$total_amount",
                            0
                        ]
                    }
                }
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "period": "$_id",
                "jobs_count": 1,
                "revenue": 1,
                "_id": 0
            }}
        ])

        jobs_analytics = await jobs_analytics_cursor.to_list(None)

        # Users analytics - Let timezone middleware handle the conversion
        users_analytics_cursor = motor_db.users.aggregate([
            {"$match": {"created_at": {"$gte": start_date_utc}}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": date_format,
                        "date": "$created_at",
                        "timezone": "Asia/Kolkata"  # Use MongoDB's built-in timezone support
                    }
                },
                "new_users": {"$sum": 1},
                "new_providers": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["provider", "$roles"]},
                            1,
                            0
                        ]
                    }
                }
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "period": "$_id",
                "new_users": 1,
                "new_providers": 1,
                "_id": 0
            }}
        ])

        users_analytics = await users_analytics_cursor.to_list(None)

        return {
            "status": "success",
            "data": {
                "timeframe": timeframe,
                "jobs": jobs_analytics,
                "users": users_analytics,
                "generated_at": now_ist.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error in get_analytics_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics data")
