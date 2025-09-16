# Services Architecture

This documents the services layer of Workerlly. Main thing to know is that most of the "services" are actually just notification handling - the rest of the business logic is scattered throughout the API endpoints.

## What's Actually in Services

```
app/services/
├── notification_hub.py          # Main notification handler (1333 lines, bit messy)
├── notification_channels.py     # WebSocket + FCM delivery (484 lines)  
├── notification_analytics.py    # Basic tracking (244 lines)
├── firebase_service.py          # FCM wrapper (125 lines)
├── redis_service.py             # Job notification caching (287 lines)
├── job_service.py               # Empty - never implemented
└── user_service.py              # Empty - never implemented
```

## Notification Hub

This is the main service that handles all notifications. Uses singleton pattern which is fine for this use case. The implementation is pretty straightforward but limited.

### What Events It Actually Handles

Only 6 event types are registered:

```python
# Job Events
"new_job"              # Broadcast to seekers by category+city
"job_rate_update"      # Real-time updates only
"remove_job"           # Real-time removal

# Bid Events  
"NEW_BID"              # To job owner
"BID_ACCEPTED"         # To specific user
"BID_REJECTED"         # To specific user
```

Note: A lot of the documentation mentions other events like `JOB_STARTED`, `JOB_COMPLETED`, etc. but they're not actually implemented. The system is simpler than it looks.

### Delivery Strategies

4 strategies available:

```python
"websocket_first_fcm_fallback"    # Try WebSocket first, FCM if that fails
"websocket_only"                  # WebSocket only
"fcm_only"                        # FCM only (rarely used)
"both"                            # Both channels at same time
```

The fallback strategy works pretty well in practice. WebSocket is faster when users are active, FCM ensures delivery when they're not.

### How Recipients Are Found

Pretty basic recipient resolution:

```python
async def _get_seekers_by_category_city(self, context, data):
    """Find seekers by category and city"""
    seekers = await motor_db.user_stats.find({
        "seeker_stats": {"$exists": True},
        "seeker_stats.city_id": ObjectId(city_id),
        "seeker_stats.category.category_id": ObjectId(category_id)
    }).to_list(length=None)
    
    return [str(seeker["user_id"]) for seeker in seekers]
```

No fancy filtering by availability, distance, ratings, etc. Just basic category+city matching.

## Notification Channels

Handles the actual delivery through WebSocket and FCM.

### WebSocket Channel

```python
async def send_websocket(self, user_id: str, event_type: str, data: Dict) -> bool:
    # Uses "OLD FORMAT" for backward compatibility
    message = {
        "type": event_type,  # Direct event type
        "data": data         # Raw data
    }
    
    await manager.send_personal_message(message, user_id)
    return True
```

Important: Uses "OLD FORMAT" because changing it would break the mobile apps. The WebSocket manager expects this exact structure.

### FCM Channel

Firebase push notifications with some token cleanup:

```python
async def send_fcm(self, user_id: str, title: str, body: str, data: Dict, target_app: str = "seeker") -> bool:
    # Get tokens from fcm_tokens collection
    fcm_tokens = await self._get_user_fcm_tokens(user_id, target_app)
    
    # All FCM data values must be strings
    fcm_data = {
        **{k: str(v) for k, v in data.items()},
        "timestamp": datetime.utcnow().isoformat(),
        "click_action": "FLUTTER_NOTIFICATION_CLICK"
    }
    
    result = await self.firebase_service.send_notification(tokens, title, body, fcm_data)
    
    # Clean up failed tokens
    if result.get("failed_tokens"):
        await self._cleanup_failed_tokens(result["failed_tokens"])
    
    return result.get("success", 0) > 0
```

FCM is finicky about data types - everything has to be a string or it fails silently.

## Firebase Service

Wrapper around Firebase Admin SDK. Has dual credential loading which is useful:

```python
def __init__(self):
    try:
        # Try environment variable first (Docker)
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_creds:
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to file (local dev)
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        raise e
```

The heads-up notification config is important for Android:

```python
message = messaging.MulticastMessage(
    tokens=tokens,
    notification=messaging.Notification(title=title, body=body),
    data=data,
    android=messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id="high_importance_channel",
            priority="high"
        )
    ),
    apns=messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                sound="default",
                badge=1,
                content_available=True
            )
        )
    )
)
```

## Redis Service

Caches job notifications by category and city for 6 minutes. Has a relay system that re-broadcasts jobs after 2 minutes.

### Job Notification Storage

```python
async def store_job_notification(self, job_data: dict, user_id: str = None):
    notification_data = {
        "type": "new_job",
        "data": {
            "id": str(job_data["_id"]),
            "sub_category": await get_sub_category_name(job_data["sub_category_ids"][0]),
            "location": f"{job_data['address_snapshot']['label']}, {city_name}",
            "hourly_rate": job_data["hourly_rate"],
            "user_id": str(user_id) if user_id else None
        }
    }
    
    # Store in Redis with category:city key
    redis_key = f"job_notifications:{category_id}:{city_id}"
    
    await self.redis_manager.zadd(
        redis_key,
        {json.dumps(notification_data): int(datetime.utcnow().timestamp())}
    )
    
    # Expire after 6 minutes
    await self.redis_manager.expire(redis_key, settings.JOB_CACHE_EXPIRY)
```

### Job Relay System

There's a relay system that re-broadcasts jobs after 1 minute. Uses Redis key expiration events:

```python
async def schedule_job_relay(self, job_id: str, notification_data: dict, category_id: str, city_id: str):
    relay_key = f"job_relay:{job_id}"
    relay_data = {
        "notification": notification_data,
        "category_id": str(category_id),
        "city_id": str(city_id)
    }
    
    await self.redis_manager.set(relay_key, json.dumps(relay_data))
    await self.redis_manager.expire(relay_key, 120)  # 2 minutes
```

A separate Redis subscriber listens for these expiration events and re-broadcasts the jobs. It's a bit convoluted but works.

## Analytics

Very basic analytics that only tracks delivery success/failure:

```python
async def record_delivery(self, event_type: str, context: Dict, delivery_report: Dict):
    analytics_data = {
        "event_type": event_type,
        "user_id": context.get("user_id"),
        "delivery_status": delivery_report.get("status", "unknown"),
        "channels_used": delivery_report.get("channels", []),
        "delivery_time": datetime.utcnow(),
        "success_count": delivery_report.get("success_count", 0),
        "failure_count": delivery_report.get("failure_count", 0)
    }
    
    await motor_db.notification_analytics.insert_one(analytics_data)
```

No click tracking, open rates, or engagement metrics. Just basic delivery stats.

## What's Missing

A few things that could be improved:

1. **Better recipient filtering** - Currently just matches category+city, could add distance, availability, ratings
2. **Click/open tracking** - Analytics are very basic
3. **Notification preferences** - Users can't configure what notifications they want
4. **Rate limiting** - No protection against notification spam
5. **Template system** - Notification text is hardcoded in event registration

## Performance Notes

- Redis caching works well for job notifications
- WebSocket connections are managed globally, not per-service
- FCM token cleanup is important to avoid hitting rate limits
- The singleton pattern for NotificationHub is fine since it's stateless

Overall the notification system works but it's fairly basic. The main complexity is in the delivery strategies and Redis caching.