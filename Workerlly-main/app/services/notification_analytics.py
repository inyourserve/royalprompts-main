# app/services/notification_analytics.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from app.db.models.database import motor_db

logger = logging.getLogger(__name__)


class NotificationAnalytics:
    """
    Analytics service for tracking notification delivery and performance
    """

    def __init__(self):
        self.collection = motor_db.notification_analytics

    async def record_delivery(
            self,
            event_type: str,
            context: Dict[str, Any],
            delivery_report: Dict[str, Any]
    ):
        """Record notification delivery statistics"""
        try:
            record = {
                "event_type": event_type,
                "timestamp": datetime.utcnow(),
                "context": context,
                "delivery": {
                    "websocket_count": delivery_report["websocket_count"],
                    "fcm_count": delivery_report["fcm_count"],
                    "failure_count": delivery_report["failure_count"],
                    "total_recipients": delivery_report["total_recipients"],
                    "success_rate": delivery_report["success_rate"]
                },
                # Store user lists for debugging (optional)
                "recipients": {
                    "websocket_users": delivery_report["websocket_sent"],
                    "fcm_users": delivery_report["fcm_sent"],
                    "failed_users": delivery_report["failed_deliveries"]
                }
            }

            await self.collection.insert_one(record)
            logger.debug(f"Analytics recorded for {event_type}")

        except Exception as e:
            logger.error(f"Error recording analytics: {str(e)}")

    async def get_stats(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated notification statistics"""
        try:
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Build match criteria
            match_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
            if event_type:
                match_criteria["event_type"] = event_type

            # Aggregation pipeline
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": "$event_type",
                        "total_notifications": {"$sum": 1},
                        "total_recipients": {"$sum": "$delivery.total_recipients"},
                        "total_websocket": {"$sum": "$delivery.websocket_count"},
                        "total_fcm": {"$sum": "$delivery.fcm_count"},
                        "total_failures": {"$sum": "$delivery.failure_count"},
                        "avg_success_rate": {"$avg": "$delivery.success_rate"}
                    }
                },
                {
                    "$project": {
                        "event_type": "$_id",
                        "total_notifications": 1,
                        "total_recipients": 1,
                        "total_websocket": 1,
                        "total_fcm": 1,
                        "total_failures": 1,
                        "avg_success_rate": {"$round": ["$avg_success_rate", 2]},
                        "websocket_percentage": {
                            "$round": [
                                {"$multiply": [
                                    {"$divide": ["$total_websocket", "$total_recipients"]},
                                    100
                                ]},
                                2
                            ]
                        },
                        "fcm_percentage": {
                            "$round": [
                                {"$multiply": [
                                    {"$divide": ["$total_fcm", "$total_recipients"]},
                                    100
                                ]},
                                2
                            ]
                        }
                    }
                },
                {"$sort": {"total_notifications": -1}}
            ]

            results = await self.collection.aggregate(pipeline).to_list(length=None)

            # Get overall summary
            overall_summary = await self._get_overall_summary(match_criteria)

            return {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "by_event_type": results,
                "overall_summary": overall_summary
            }

        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            return {"by_event_type": [], "overall_summary": {}}

    async def _get_overall_summary(self, match_criteria: Dict) -> Dict[str, Any]:
        """Get overall summary across all event types"""
        try:
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": None,
                        "total_notifications": {"$sum": 1},
                        "total_recipients": {"$sum": "$delivery.total_recipients"},
                        "total_websocket": {"$sum": "$delivery.websocket_count"},
                        "total_fcm": {"$sum": "$delivery.fcm_count"},
                        "total_failures": {"$sum": "$delivery.failure_count"}
                    }
                }
            ]

            result = await self.collection.aggregate(pipeline).to_list(length=1)

            if result:
                summary = result[0]
                total_recipients = summary["total_recipients"]

                return {
                    "total_notifications": summary["total_notifications"],
                    "total_recipients": total_recipients,
                    "total_websocket": summary["total_websocket"],
                    "total_fcm": summary["total_fcm"],
                    "total_failures": summary["total_failures"],
                    "overall_success_rate": round(
                        ((summary["total_websocket"] + summary["total_fcm"]) / total_recipients * 100)
                        if total_recipients > 0 else 0, 2
                    ),
                    "websocket_percentage": round(
                        (summary["total_websocket"] / total_recipients * 100)
                        if total_recipients > 0 else 0, 2
                    ),
                    "fcm_percentage": round(
                        (summary["total_fcm"] / total_recipients * 100)
                        if total_recipients > 0 else 0, 2
                    ),
                    "estimated_fcm_cost": round(summary["total_fcm"] * 0.0005, 3)  # Estimate $0.0005 per FCM
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting overall summary: {str(e)}")
            return {}

    async def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily breakdown of notification stats"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"}
                        },
                        "total_notifications": {"$sum": 1},
                        "total_websocket": {"$sum": "$delivery.websocket_count"},
                        "total_fcm": {"$sum": "$delivery.fcm_count"},
                        "total_failures": {"$sum": "$delivery.failure_count"}
                    }
                },
                {
                    "$project": {
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month",
                                "day": "$_id.day"
                            }
                        },
                        "total_notifications": 1,
                        "total_websocket": 1,
                        "total_fcm": 1,
                        "total_failures": 1
                    }
                },
                {"$sort": {"date": 1}}
            ]

            results = await self.collection.aggregate(pipeline).to_list(length=None)

            # Format results
            daily_stats = []
            for result in results:
                daily_stats.append({
                    "date": result["date"].strftime("%Y-%m-%d"),
                    "total_notifications": result["total_notifications"],
                    "websocket_sent": result["total_websocket"],
                    "fcm_sent": result["total_fcm"],
                    "failures": result["total_failures"]
                })

            return daily_stats

        except Exception as e:
            logger.error(f"Error getting daily stats: {str(e)}")
            return []
