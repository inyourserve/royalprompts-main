# v4 app/services/notification_hub.py

import logging
from typing import Dict, Any, List, Callable

from bson import ObjectId

from app.db.models.database import motor_db
from app.services.notification_analytics import NotificationAnalytics
from app.services.notification_channels import NotificationChannels

logger = logging.getLogger(__name__)


class NotificationHub:
    """
    Central notification hub for Workerlly
    Handles all notifications with smart routing and fallback
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationHub, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.channels = NotificationChannels()
            self.analytics = NotificationAnalytics()
            self.events = {}  # Event type registry
            self.recipient_resolvers = {}  # Who gets what notifications
            self._register_workerlly_events()
            self._initialized = True
            logger.info("Notification Hub initialized")

    def _register_workerlly_events(self):
        """Register all Workerlly notification events"""

        # Job events - Using OLD format with routing
        self.register_event(
            event_type="new_job",
            recipient_resolver=self._get_seekers_by_category_city,
            delivery_strategy="both",
            title_template="New Job Available",
            body_template="New {sub_category} job available in {location}",
            route="/homeScreen",
            route_params={"job_id": "id"}
        )

        self.register_event(
            event_type="job_rate_update",
            recipient_resolver=self._get_seekers_by_category_city,
            delivery_strategy="websocket_only",
            title_template="Job Rate Updated",
            body_template="Rate updated to ₹{hourly_rate}/hr for {sub_category} job",
            route="/homeScreen",
            route_params={"job_id": "id"}
        )

        self.register_event(
            event_type="remove_job",
            recipient_resolver=self._get_seekers_by_category_city,
            delivery_strategy="websocket_only",
            title_template="Job Cancelled",
            body_template="Job has been cancelled",
            route="/jobs-list",
            route_params={}
        )

        # Bid events
        self.register_event(
            event_type="NEW_BID",
            recipient_resolver=self._get_job_owner,
            delivery_strategy="websocket_first_fcm_fallback",
            title_template="New Bid Received",
            body_template="{seeker_name} placed a bid of ₹{amount} on your job",
            route="/bid-details",
            route_params={"bid_id": "bid_id", "job_id": "job_id"}
        )

        self.register_event(
            event_type="BID_ACCEPTED",
            recipient_resolver=self._get_specific_user,
            delivery_strategy="websocket_first_fcm_fallback",
            title_template="Bid Accepted! 🎉",
            body_template="Your bid has been accepted",
            route="/job-tracking",
            route_params={"job_id": "job_id"}
        )

        self.register_event(
            event_type="BID_REJECTED",
            recipient_resolver=self._get_specific_user,
            delivery_strategy="websocket_first_fcm_fallback",
            title_template="Bid Update",
            body_template="Your bid was not selected",
            route="/jobs-list",
            route_params={}
        )

    def register_event(
            self,
            event_type: str,
            recipient_resolver: Callable,
            delivery_strategy: str,
            title_template: str,
            body_template: str,
            route: str = "/home",
            route_params: Dict[str, str] = None
    ):
        """Register a new notification event type with routing"""
        self.events[event_type] = {
            "recipient_resolver": recipient_resolver,
            "delivery_strategy": delivery_strategy,
            "title_template": title_template,
            "body_template": body_template,
            "route": route,
            "route_params": route_params or {}
        }
        logger.debug(f"Registered event: {event_type}")

    async def send(
            self,
            event_type: str,
            data: Dict[str, Any],
            context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Central method to send any notification

        Args:
            event_type: Type of notification (new_job, remove_job, etc.)
            data: Notification data
            context: Context for recipient resolution (category_id, city_id, user_id, etc.)

        Returns:
            Delivery report with success/failure counts
        """
        try:
            if event_type not in self.events:
                raise ValueError(f"Unknown event type: {event_type}")

            event_config = self.events[event_type]
            context = context or {}

            logger.info(f"Processing {event_type} notification")

            # 1. Resolve recipients
            recipients = await event_config["recipient_resolver"](context, data)

            if not recipients:
                logger.warning(f"No recipients found for {event_type}")
                return {"success": False, "reason": "no_recipients"}

            # 2. Generate title and body
            title = event_config["title_template"].format(**data, **context)
            body = event_config["body_template"].format(**data, **context)

            # 3. Prepare routing data for FCM (only for FCM, not WebSocket)
            routing_data = {
                "route": event_config["route"],
                "notification_type": event_type
            }

            # Add route parameters from data
            for param_name, data_field in event_config["route_params"].items():
                if data_field in data:
                    routing_data[param_name] = str(data[data_field])

            # 4. Send notifications based on strategy
            delivery_report = await self._send_with_strategy(
                strategy=event_config["delivery_strategy"],
                recipients=recipients,
                event_type=event_type,
                data=data,
                title=title,
                body=body,
                routing_data=routing_data
            )

            # 5. Record analytics
            await self.analytics.record_delivery(
                event_type=event_type,
                context=context,
                delivery_report=delivery_report
            )

            logger.info(
                f"{event_type} notification sent: WS={delivery_report['websocket_count']}, FCM={delivery_report['fcm_count']}")
            return {"success": True, "delivery_report": delivery_report}

        except Exception as e:
            logger.error(f"Error sending {event_type} notification: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _send_with_strategy(
            self,
            strategy: str,
            recipients: List[str],
            event_type: str,
            data: Dict[str, Any],
            title: str,
            body: str,
            routing_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send notifications using specified delivery strategy"""

        websocket_sent = []
        fcm_sent = []
        failed_deliveries = []
        routing_data = routing_data or {}

        for recipient_id in recipients:
            try:
                if strategy == "websocket_first_fcm_fallback":
                    # Try WebSocket first (clean data, no routing)
                    websocket_success = await self.channels.send_websocket(
                        user_id=recipient_id,
                        event_type=event_type,
                        data=data
                    )

                    if websocket_success:
                        websocket_sent.append(recipient_id)
                    else:
                        # WebSocket failed, try FCM (with routing data)
                        fcm_success = await self.channels.send_fcm(
                            user_id=recipient_id,
                            title=title,
                            body=body,
                            data={**data, **routing_data}
                        )

                        if fcm_success:
                            fcm_sent.append(recipient_id)
                        else:
                            failed_deliveries.append(recipient_id)

                elif strategy == "fcm_only":
                    fcm_success = await self.channels.send_fcm(
                        user_id=recipient_id,
                        title=title,
                        body=body,
                        data={**data, **routing_data}
                    )

                    if fcm_success:
                        fcm_sent.append(recipient_id)
                    else:
                        failed_deliveries.append(recipient_id)

                elif strategy == "websocket_only":
                    websocket_success = await self.channels.send_websocket(
                        user_id=recipient_id,
                        event_type=event_type,
                        data=data
                    )

                    if websocket_success:
                        websocket_sent.append(recipient_id)
                    else:
                        failed_deliveries.append(recipient_id)

                elif strategy == "both":
                    # Send to WebSocket (clean data)
                    websocket_success = await self.channels.send_websocket(
                        user_id=recipient_id,
                        event_type=event_type,
                        data=data
                    )

                    # Send to FCM (with routing data)
                    fcm_success = await self.channels.send_fcm(
                        user_id=recipient_id,
                        title=title,
                        body=body,
                        data={**data, **routing_data}
                    )

                    if websocket_success:
                        websocket_sent.append(recipient_id)

                    if fcm_success:
                        fcm_sent.append(recipient_id)

                    # Only mark as failed if BOTH channels failed
                    if not websocket_success and not fcm_success:
                        failed_deliveries.append(recipient_id)

            except Exception as e:
                logger.error(f"Error sending to {recipient_id}: {str(e)}")
                failed_deliveries.append(recipient_id)

        return {
            "websocket_sent": websocket_sent,
            "fcm_sent": fcm_sent,
            "failed_deliveries": failed_deliveries,
            "websocket_count": len(websocket_sent),
            "fcm_count": len(fcm_sent),
            "failure_count": len(failed_deliveries),
            "total_recipients": len(recipients),
            "success_rate": ((len(websocket_sent) + len(fcm_sent)) / len(recipients)) * 100
        }

    # Recipient resolver methods
    async def _get_seekers_by_category_city(self, context: Dict, data: Dict) -> List[str]:
        """Get seekers from user_stats based on category and city only"""
        try:
            category_id = context.get("category_id")
            city_id = context.get("city_id")

            if not category_id or not city_id:
                return []

            # Query user_stats collection - category + city only
            seekers = await motor_db.user_stats.find({
                "seeker_stats": {"$exists": True},  # User is a seeker
                "seeker_stats.city_id": ObjectId(city_id),  # Same city
                "seeker_stats.category.category_id": ObjectId(category_id)  # Same category only
            }).to_list(length=None)

            return [str(seeker["user_id"]) for seeker in seekers]

        except Exception as e:
            logger.error(f"Error getting seekers by category/city: {str(e)}")
            return []

    async def _get_job_owner(self, context: Dict, data: Dict) -> List[str]:
        """Get job owner for bid notifications"""
        try:
            job_id = context.get("job_id") or data.get("job_id")
            if not job_id:
                return []

            job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
            if job:
                return [str(job["user_id"])]
            return []

        except Exception as e:
            logger.error(f"Error getting job owner: {str(e)}")
            return []

    async def _get_specific_user(self, context: Dict, data: Dict) -> List[str]:
        """Get specific user from context"""
        try:
            user_id = context.get("user_id") or data.get("user_id")
            if user_id:
                return [str(user_id)]
            return []

        except Exception as e:
            logger.error(f"Error getting specific user: {str(e)}")
            return []


# Singleton instance
_notification_hub = None


def get_notification_hub() -> NotificationHub:
    global _notification_hub
    if _notification_hub is None:
        _notification_hub = NotificationHub()
    return _notification_hub

# # v3 app/services/notification_hub.py
#
# import logging
# from typing import Dict, Any, List, Callable
#
# from bson import ObjectId
#
# from app.db.models.database import motor_db
# from app.services.notification_analytics import NotificationAnalytics
# from app.services.notification_channels import NotificationChannels
#
# logger = logging.getLogger(__name__)
#
#
# class NotificationHub:
#     """
#     Central notification hub for Workerlly
#     Handles all notifications with smart routing and fallback
#     """
#
#     _instance = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(NotificationHub, cls).__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance
#
#     def __init__(self):
#         if not self._initialized:
#             self.channels = NotificationChannels()
#             self.analytics = NotificationAnalytics()
#             self.events = {}  # Event type registry
#             self.recipient_resolvers = {}  # Who gets what notifications
#             self._register_workerlly_events()
#             self._initialized = True
#             logger.info("Notification Hub initialized")
#
#     def _register_workerlly_events(self):
#         """Register all Workerlly notification events"""
#
#         # Job events - Using OLD format
#         self.register_event(
#             event_type="new_job",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Job Available",
#             body_template="New {sub_category} job available in {location}"
#         )
#
#         self.register_event(
#             event_type="job_rate_update",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Job Rate Updated",
#             body_template="Rate updated to ₹{hourly_rate}/hr for {sub_category} job"
#         )
#
#         self.register_event(
#             event_type="remove_job",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_only",
#             title_template="Job Cancelled",
#             body_template="Job has been cancelled"
#         )
#
#         # Bid events
#         self.register_event(
#             event_type="NEW_BID",
#             recipient_resolver=self._get_job_owner,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Bid Received",
#             body_template="{seeker_name} placed a bid of ₹{amount} on your job"
#         )
#
#         self.register_event(
#             event_type="BID_ACCEPTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Accepted! 🎉",
#             body_template="Your bid has been accepted"
#         )
#
#         self.register_event(
#             event_type="BID_REJECTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Update",
#             body_template="Your bid was not selected"
#         )
#
#     def register_event(
#             self,
#             event_type: str,
#             recipient_resolver: Callable,
#             delivery_strategy: str,
#             title_template: str,
#             body_template: str
#     ):
#         """Register a new notification event type"""
#         self.events[event_type] = {
#             "recipient_resolver": recipient_resolver,
#             "delivery_strategy": delivery_strategy,
#             "title_template": title_template,
#             "body_template": body_template
#         }
#         logger.debug(f"Registered event: {event_type}")
#
#     async def send(
#             self,
#             event_type: str,
#             data: Dict[str, Any],
#             context: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """
#         Central method to send any notification
#
#         Args:
#             event_type: Type of notification (new_job, remove_job, etc.)
#             data: Notification data
#             context: Context for recipient resolution (category_id, city_id, user_id, etc.)
#
#         Returns:
#             Delivery report with success/failure counts
#         """
#         try:
#             if event_type not in self.events:
#                 raise ValueError(f"Unknown event type: {event_type}")
#
#             event_config = self.events[event_type]
#             context = context or {}
#
#             logger.info(f"Processing {event_type} notification")
#
#             # 1. Resolve recipients
#             recipients = await event_config["recipient_resolver"](context, data)
#
#             if not recipients:
#                 logger.warning(f"No recipients found for {event_type}")
#                 return {"success": False, "reason": "no_recipients"}
#
#             # 2. Generate title and body
#             title = event_config["title_template"].format(**data, **context)
#             body = event_config["body_template"].format(**data, **context)
#
#             # 3. Send notifications based on strategy
#             delivery_report = await self._send_with_strategy(
#                 strategy=event_config["delivery_strategy"],
#                 recipients=recipients,
#                 event_type=event_type,
#                 data=data,
#                 title=title,
#                 body=body
#             )
#
#             # 4. Record analytics
#             await self.analytics.record_delivery(
#                 event_type=event_type,
#                 context=context,
#                 delivery_report=delivery_report
#             )
#
#             logger.info(
#                 f"{event_type} notification sent: WS={delivery_report['websocket_count']}, FCM={delivery_report['fcm_count']}")
#             return {"success": True, "delivery_report": delivery_report}
#
#         except Exception as e:
#             logger.error(f"Error sending {event_type} notification: {str(e)}")
#             return {"success": False, "error": str(e)}
#
#     async def _send_with_strategy(
#             self,
#             strategy: str,
#             recipients: List[str],
#             event_type: str,
#             data: Dict[str, Any],
#             title: str,
#             body: str
#     ) -> Dict[str, Any]:
#         """Send notifications using specified delivery strategy"""
#
#         websocket_sent = []
#         fcm_sent = []
#         failed_deliveries = []
#
#         for recipient_id in recipients:
#             try:
#                 if strategy == "websocket_first_fcm_fallback":
#                     # Try WebSocket first
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         # WebSocket failed, try FCM
#                         fcm_success = await self.channels.send_fcm(
#                             user_id=recipient_id,
#                             title=title,
#                             body=body,
#                             data=data
#                         )
#
#                         if fcm_success:
#                             fcm_sent.append(recipient_id)
#                         else:
#                             failed_deliveries.append(recipient_id)
#
#                 elif strategy == "fcm_only":
#                     fcm_success = await self.channels.send_fcm(
#                         user_id=recipient_id,
#                         title=title,
#                         body=body,
#                         data=data
#                     )
#
#                     if fcm_success:
#                         fcm_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#                 elif strategy == "websocket_only":
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#                 elif strategy == "both":
#                     # Send to both WebSocket AND FCM regardless of WebSocket success
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     fcm_success = await self.channels.send_fcm(
#                         user_id=recipient_id,
#                         title=title,
#                         body=body,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#
#                     if fcm_success:
#                         fcm_sent.append(recipient_id)
#
#                     # Only mark as failed if BOTH channels failed
#                     if not websocket_success and not fcm_success:
#                         failed_deliveries.append(recipient_id)
#
#             except Exception as e:
#                 logger.error(f"Error sending to {recipient_id}: {str(e)}")
#                 failed_deliveries.append(recipient_id)
#
#         return {
#             "websocket_sent": websocket_sent,
#             "fcm_sent": fcm_sent,
#             "failed_deliveries": failed_deliveries,
#             "websocket_count": len(websocket_sent),
#             "fcm_count": len(fcm_sent),
#             "failure_count": len(failed_deliveries),
#             "total_recipients": len(recipients),
#             "success_rate": ((len(websocket_sent) + len(fcm_sent)) / len(recipients)) * 100
#         }
#
#     # Recipient resolver methods
#     async def _get_seekers_by_category_city(self, context: Dict, data: Dict) -> List[str]:
#         """Get seekers from user_stats based on category and city only"""
#         try:
#             category_id = context.get("category_id")
#             city_id = context.get("city_id")
#
#             if not category_id or not city_id:
#                 return []
#
#             # Query user_stats collection - category + city only
#             seekers = await motor_db.user_stats.find({
#                 "seeker_stats": {"$exists": True},  # User is a seeker
#                 "seeker_stats.city_id": ObjectId(city_id),  # Same city
#                 "seeker_stats.category.category_id": ObjectId(category_id)  # Same category only
#             }).to_list(length=None)
#
#             return [str(seeker["user_id"]) for seeker in seekers]
#
#         except Exception as e:
#             logger.error(f"Error getting seekers by category/city: {str(e)}")
#             return []
#
#     async def _get_job_owner(self, context: Dict, data: Dict) -> List[str]:
#         """Get job owner for bid notifications"""
#         try:
#             job_id = context.get("job_id") or data.get("job_id")
#             if not job_id:
#                 return []
#
#             job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#             if job:
#                 return [str(job["user_id"])]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting job owner: {str(e)}")
#             return []
#
#     async def _get_specific_user(self, context: Dict, data: Dict) -> List[str]:
#         """Get specific user from context"""
#         try:
#             user_id = context.get("user_id") or data.get("user_id")
#             if user_id:
#                 return [str(user_id)]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting specific user: {str(e)}")
#             return []
#
#
# # Singleton instance
# _notification_hub = None
#
#
# def get_notification_hub() -> NotificationHub:
#     global _notification_hub
#     if _notification_hub is None:
#         _notification_hub = NotificationHub()
#     return _notification_hub

# # v2 app/services/notification_hub.py

# import logging
# from typing import Dict, Any, List, Callable
#
# from bson import ObjectId
#
# from app.db.models.database import motor_db
# from app.services.notification_analytics import NotificationAnalytics
# from app.services.notification_channels import NotificationChannels
#
# logger = logging.getLogger(__name__)
#
#
# class NotificationHub:
#     """
#     Central notification hub for Workerlly
#     Handles all notifications with smart routing and fallback
#     """
#
#     _instance = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(NotificationHub, cls).__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance
#
#     def __init__(self):
#         if not self._initialized:
#             self.channels = NotificationChannels()
#             self.analytics = NotificationAnalytics()
#             self.events = {}  # Event type registry
#             self.recipient_resolvers = {}  # Who gets what notifications
#             self._register_workerlly_events()
#             self._initialized = True
#             logger.info("Notification Hub initialized")
#
#     def _register_workerlly_events(self):
#         """Register all Workerlly notification events"""
#
#         # Job events - Using OLD format
#         self.register_event(
#             event_type="new_job",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Job Available",
#             body_template="New {sub_category} job available in {location}"
#         )
#
#         self.register_event(
#             event_type="job_rate_update",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Job Rate Updated",
#             body_template="Rate updated to ₹{hourly_rate}/hr for {sub_category} job"
#         )
#
#         self.register_event(
#             event_type="remove_job",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Job Cancelled",
#             body_template="Job has been cancelled"
#         )
#
#         # Bid events
#         self.register_event(
#             event_type="NEW_BID",
#             recipient_resolver=self._get_job_owner,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Bid Received",
#             body_template="{seeker_name} placed a bid of ₹{amount} on your job"
#         )
#
#         self.register_event(
#             event_type="BID_ACCEPTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Accepted! 🎉",
#             body_template="Your bid has been accepted"
#         )
#
#         self.register_event(
#             event_type="BID_REJECTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Update",
#             body_template="Your bid was not selected"
#         )
#
#     def register_event(
#             self,
#             event_type: str,
#             recipient_resolver: Callable,
#             delivery_strategy: str,
#             title_template: str,
#             body_template: str
#     ):
#         """Register a new notification event type"""
#         self.events[event_type] = {
#             "recipient_resolver": recipient_resolver,
#             "delivery_strategy": delivery_strategy,
#             "title_template": title_template,
#             "body_template": body_template
#         }
#         logger.debug(f"Registered event: {event_type}")
#
#     async def send(
#             self,
#             event_type: str,
#             data: Dict[str, Any],
#             context: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """
#         Central method to send any notification
#
#         Args:
#             event_type: Type of notification (new_job, remove_job, etc.)
#             data: Notification data
#             context: Context for recipient resolution (category_id, city_id, user_id, etc.)
#
#         Returns:
#             Delivery report with success/failure counts
#         """
#         try:
#             if event_type not in self.events:
#                 raise ValueError(f"Unknown event type: {event_type}")
#
#             event_config = self.events[event_type]
#             context = context or {}
#
#             logger.info(f"Processing {event_type} notification")
#
#             # 1. Resolve recipients
#             recipients = await event_config["recipient_resolver"](context, data)
#
#             if not recipients:
#                 logger.warning(f"No recipients found for {event_type}")
#                 return {"success": False, "reason": "no_recipients"}
#
#             # 2. Generate title and body
#             title = event_config["title_template"].format(**data, **context)
#             body = event_config["body_template"].format(**data, **context)
#
#             # 3. Send notifications based on strategy
#             delivery_report = await self._send_with_strategy(
#                 strategy=event_config["delivery_strategy"],
#                 recipients=recipients,
#                 event_type=event_type,
#                 data=data,
#                 title=title,
#                 body=body
#             )
#
#             # 4. Record analytics
#             await self.analytics.record_delivery(
#                 event_type=event_type,
#                 context=context,
#                 delivery_report=delivery_report
#             )
#
#             logger.info(
#                 f"{event_type} notification sent: WS={delivery_report['websocket_count']}, FCM={delivery_report['fcm_count']}")
#             return {"success": True, "delivery_report": delivery_report}
#
#         except Exception as e:
#             logger.error(f"Error sending {event_type} notification: {str(e)}")
#             return {"success": False, "error": str(e)}
#
#     async def _send_with_strategy(
#             self,
#             strategy: str,
#             recipients: List[str],
#             event_type: str,
#             data: Dict[str, Any],
#             title: str,
#             body: str
#     ) -> Dict[str, Any]:
#         """Send notifications using specified delivery strategy"""
#
#         websocket_sent = []
#         fcm_sent = []
#         failed_deliveries = []
#
#         for recipient_id in recipients:
#             try:
#                 if strategy == "websocket_first_fcm_fallback":
#                     # Try WebSocket first
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         # WebSocket failed, try FCM
#                         fcm_success = await self.channels.send_fcm(
#                             user_id=recipient_id,
#                             title=title,
#                             body=body,
#                             data=data
#                         )
#
#                         if fcm_success:
#                             fcm_sent.append(recipient_id)
#                         else:
#                             failed_deliveries.append(recipient_id)
#
#                 elif strategy == "fcm_only":
#                     fcm_success = await self.channels.send_fcm(
#                         user_id=recipient_id,
#                         title=title,
#                         body=body,
#                         data=data
#                     )
#
#                     if fcm_success:
#                         fcm_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#                 elif strategy == "websocket_only":
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#             except Exception as e:
#                 logger.error(f"Error sending to {recipient_id}: {str(e)}")
#                 failed_deliveries.append(recipient_id)
#
#         return {
#             "websocket_sent": websocket_sent,
#             "fcm_sent": fcm_sent,
#             "failed_deliveries": failed_deliveries,
#             "websocket_count": len(websocket_sent),
#             "fcm_count": len(fcm_sent),
#             "failure_count": len(failed_deliveries),
#             "total_recipients": len(recipients),
#             "success_rate": ((len(websocket_sent) + len(fcm_sent)) / len(recipients)) * 100
#         }
#
#     # Recipient resolver methods
#     async def _get_seekers_by_category_city(self, context: Dict, data: Dict) -> List[str]:
#         """Get seekers from user_stats based on category and city only"""
#         try:
#             category_id = context.get("category_id")
#             city_id = context.get("city_id")
#
#             if not category_id or not city_id:
#                 return []
#
#             # Query user_stats collection - category + city only
#             seekers = await motor_db.user_stats.find({
#                 "seeker_stats": {"$exists": True},  # User is a seeker
#                 "seeker_stats.city_id": ObjectId(city_id),  # Same city
#                 "seeker_stats.category.category_id": ObjectId(category_id)  # Same category only
#             }).to_list(length=None)
#
#             return [str(seeker["user_id"]) for seeker in seekers]
#
#         except Exception as e:
#             logger.error(f"Error getting seekers by category/city: {str(e)}")
#             return []
#
#     async def _get_job_owner(self, context: Dict, data: Dict) -> List[str]:
#         """Get job owner for bid notifications"""
#         try:
#             job_id = context.get("job_id") or data.get("job_id")
#             if not job_id:
#                 return []
#
#             job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#             if job:
#                 return [str(job["user_id"])]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting job owner: {str(e)}")
#             return []
#
#     async def _get_specific_user(self, context: Dict, data: Dict) -> List[str]:
#         """Get specific user from context"""
#         try:
#             user_id = context.get("user_id") or data.get("user_id")
#             if user_id:
#                 return [str(user_id)]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting specific user: {str(e)}")
#             return []
#
#
# # Singleton instance
# _notification_hub = None
#
#
# def get_notification_hub() -> NotificationHub:
#     global _notification_hub
#     if _notification_hub is None:
#         _notification_hub = NotificationHub()
#     return _notification_hub

# # old v1 app/services/notification_hub.py
#
# import logging
# from typing import Dict, Any, List, Callable
#
# from bson import ObjectId
#
# from app.db.models.database import motor_db
# from app.services.notification_analytics import NotificationAnalytics
# from app.services.notification_channels import NotificationChannels
#
# logger = logging.getLogger(__name__)
#
#
# class NotificationHub:
#     """
#     Central notification hub for Workerlly
#     Handles all notifications with smart routing and fallback
#     """
#
#     _instance = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(NotificationHub, cls).__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance
#
#     def __init__(self):
#         if not self._initialized:
#             self.channels = NotificationChannels()
#             self.analytics = NotificationAnalytics()
#             self.events = {}  # Event type registry
#             self.recipient_resolvers = {}  # Who gets what notifications
#             self._register_workerlly_events()
#             self._initialized = True
#             logger.info("Notification Hub initialized")
#
#     def _register_workerlly_events(self):
#         """Register all Workerlly notification events"""
#
#         # Job events
#         self.register_event(
#             event_type="NEW_JOB",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Job Available",
#             body_template="New {sub_category} job available in {location}"
#         )
#
#         self.register_event(
#             event_type="JOB_RATE_UPDATE",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Job Rate Updated",
#             body_template="Rate updated to ₹{hourly_rate}/hr for {sub_category} job"
#         )
#
#         self.register_event(
#             event_type="JOB_CANCELLED",
#             recipient_resolver=self._get_seekers_by_category_city,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Job Cancelled",
#             body_template="Job has been cancelled"
#         )
#
#         # Bid events
#         self.register_event(
#             event_type="NEW_BID",
#             recipient_resolver=self._get_job_owner,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="New Bid Received",
#             body_template="{seeker_name} placed a bid of ₹{amount} on your job"
#         )
#
#         self.register_event(
#             event_type="BID_ACCEPTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Accepted! 🎉",
#             body_template="Your bid has been accepted"
#         )
#
#         self.register_event(
#             event_type="BID_REJECTED",
#             recipient_resolver=self._get_specific_user,
#             delivery_strategy="websocket_first_fcm_fallback",
#             title_template="Bid Update",
#             body_template="Your bid was not selected"
#         )
#
#     def register_event(
#             self,
#             event_type: str,
#             recipient_resolver: Callable,
#             delivery_strategy: str,
#             title_template: str,
#             body_template: str
#     ):
#         """Register a new notification event type"""
#         self.events[event_type] = {
#             "recipient_resolver": recipient_resolver,
#             "delivery_strategy": delivery_strategy,
#             "title_template": title_template,
#             "body_template": body_template
#         }
#         logger.debug(f"Registered event: {event_type}")
#
#     async def send(
#             self,
#             event_type: str,
#             data: Dict[str, Any],
#             context: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """
#         Central method to send any notification
#
#         Args:
#             event_type: Type of notification (NEW_JOB, NEW_BID, etc.)
#             data: Notification data
#             context: Context for recipient resolution (category_id, city_id, user_id, etc.)
#
#         Returns:
#             Delivery report with success/failure counts
#         """
#         try:
#             if event_type not in self.events:
#                 raise ValueError(f"Unknown event type: {event_type}")
#
#             event_config = self.events[event_type]
#             context = context or {}
#
#             logger.info(f"Processing {event_type} notification")
#
#             # 1. Resolve recipients
#             recipients = await event_config["recipient_resolver"](context, data)
#
#             if not recipients:
#                 logger.warning(f"No recipients found for {event_type}")
#                 return {"success": False, "reason": "no_recipients"}
#
#             # 2. Generate title and body
#             title = event_config["title_template"].format(**data, **context)
#             body = event_config["body_template"].format(**data, **context)
#
#             # 3. Send notifications based on strategy
#             delivery_report = await self._send_with_strategy(
#                 strategy=event_config["delivery_strategy"],
#                 recipients=recipients,
#                 event_type=event_type,
#                 data=data,
#                 title=title,
#                 body=body
#             )
#
#             # 4. Record analytics
#             await self.analytics.record_delivery(
#                 event_type=event_type,
#                 context=context,
#                 delivery_report=delivery_report
#             )
#
#             logger.info(
#                 f"{event_type} notification sent: WS={delivery_report['websocket_count']}, FCM={delivery_report['fcm_count']}")
#             return {"success": True, "delivery_report": delivery_report}
#
#         except Exception as e:
#             logger.error(f"Error sending {event_type} notification: {str(e)}")
#             return {"success": False, "error": str(e)}
#
#     async def _send_with_strategy(
#             self,
#             strategy: str,
#             recipients: List[str],
#             event_type: str,
#             data: Dict[str, Any],
#             title: str,
#             body: str
#     ) -> Dict[str, Any]:
#         """Send notifications using specified delivery strategy"""
#
#         websocket_sent = []
#         fcm_sent = []
#         failed_deliveries = []
#
#         for recipient_id in recipients:
#             try:
#                 if strategy == "websocket_first_fcm_fallback":
#                     # Try WebSocket first
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         # WebSocket failed, try FCM
#                         fcm_success = await self.channels.send_fcm(
#                             user_id=recipient_id,
#                             title=title,
#                             body=body,
#                             data=data
#                         )
#
#                         if fcm_success:
#                             fcm_sent.append(recipient_id)
#                         else:
#                             failed_deliveries.append(recipient_id)
#
#                 elif strategy == "fcm_only":
#                     fcm_success = await self.channels.send_fcm(
#                         user_id=recipient_id,
#                         title=title,
#                         body=body,
#                         data=data
#                     )
#
#                     if fcm_success:
#                         fcm_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#                 elif strategy == "websocket_only":
#                     websocket_success = await self.channels.send_websocket(
#                         user_id=recipient_id,
#                         event_type=event_type,
#                         data=data
#                     )
#
#                     if websocket_success:
#                         websocket_sent.append(recipient_id)
#                     else:
#                         failed_deliveries.append(recipient_id)
#
#             except Exception as e:
#                 logger.error(f"Error sending to {recipient_id}: {str(e)}")
#                 failed_deliveries.append(recipient_id)
#
#         return {
#             "websocket_sent": websocket_sent,
#             "fcm_sent": fcm_sent,
#             "failed_deliveries": failed_deliveries,
#             "websocket_count": len(websocket_sent),
#             "fcm_count": len(fcm_sent),
#             "failure_count": len(failed_deliveries),
#             "total_recipients": len(recipients),
#             "success_rate": ((len(websocket_sent) + len(fcm_sent)) / len(recipients)) * 100
#         }
#
#     # Recipient resolver methods
#     async def _get_seekers_by_category_city(self, context: Dict, data: Dict) -> List[str]:
#         """Get seekers from user_stats based on category and city only"""
#         try:
#             category_id = context.get("category_id")
#             city_id = context.get("city_id")
#
#             if not category_id or not city_id:
#                 return []
#
#             # Query user_stats collection - category + city only
#             seekers = await motor_db.user_stats.find({
#                 "seeker_stats": {"$exists": True},  # User is a seeker
#                 "seeker_stats.city_id": ObjectId(city_id),  # Same city
#                 "seeker_stats.category.category_id": ObjectId(category_id)  # Same category only
#             }).to_list(length=None)
#
#             return [str(seeker["user_id"]) for seeker in seekers]
#
#         except Exception as e:
#             logger.error(f"Error getting seekers by category/city: {str(e)}")
#             return []
#
#     async def _get_job_owner(self, context: Dict, data: Dict) -> List[str]:
#         """Get job owner for bid notifications"""
#         try:
#             job_id = context.get("job_id") or data.get("job_id")
#             if not job_id:
#                 return []
#
#             job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
#             if job:
#                 return [str(job["user_id"])]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting job owner: {str(e)}")
#             return []
#
#     async def _get_specific_user(self, context: Dict, data: Dict) -> List[str]:
#         """Get specific user from context"""
#         try:
#             user_id = context.get("user_id") or data.get("user_id")
#             if user_id:
#                 return [str(user_id)]
#             return []
#
#         except Exception as e:
#             logger.error(f"Error getting specific user: {str(e)}")
#             return []
#
#
# # Singleton instance
# _notification_hub = None
#
#
# def get_notification_hub() -> NotificationHub:
#     global _notification_hub
#     if _notification_hub is None:
#         _notification_hub = NotificationHub()
#     return _notification_hub
