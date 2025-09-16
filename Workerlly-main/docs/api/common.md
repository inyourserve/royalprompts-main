# Common API

Shared endpoints that work for all authenticated user types - seekers, providers, and admins.

**Base URL:** `/api/v1/common`  
**Authentication:** Any valid JWT token

## Notifications

### Get Notifications

```http
GET /api/v1/common/notifications?page=1&unread_only=true
```

Query parameters:
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 50)
- `unread_only` - Show only unread notifications (default: false)
- `type` - Filter by type: "application", "interview", "message", "system"

Response:
```json
{
    "success": true,
    "data": {
        "notifications": [
            {
                "id": "60d5ec49b4e1c8a5d8e3f1a2",
                "title": "New Application Received",
                "message": "John Doe applied for Senior Python Developer position",
                "type": "application",
                "read": false,
                "created_at": "2024-01-15T10:30:00Z",
                "data": {
                    "application_id": "60d5ec49b4e1c8a5d8e3f1a3",
                    "job_id": "60d5ec49b4e1c8a5d8e3f1a4"
                }
            }
        ],
        "unread_count": 5,
        "total": 45,
        "page": 1,
        "pages": 3
    }
}
```

### Mark as Read

```http
PATCH /api/v1/common/notifications/{notification_id}/read
```

### Mark All as Read

```http
PATCH /api/v1/common/notifications/read-all
```

### Delete Notification

```http
DELETE /api/v1/common/notifications/{notification_id}
```

## Chat System

### Get Conversations

```http
GET /api/v1/common/chat/conversations?page=1
```

Lists all conversations for the current user.

```json
{
    "success": true,
    "data": {
        "conversations": [
            {
                "id": "60d5ec49b4e1c8a5d8e3f1a2",
                "participant": {
                    "id": "60d5ec49b4e1c8a5d8e3f1a3",
                    "name": "John Doe",
                    "avatar": "https://s3.amazonaws.com/avatars/john.jpg",
                    "user_type": "seeker"
                },
                "last_message": {
                    "content": "Thanks for the interview opportunity!",
                    "sent_at": "2024-01-15T14:30:00Z",
                    "sender_id": "60d5ec49b4e1c8a5d8e3f1a3"
                },
                "unread_count": 2,
                "updated_at": "2024-01-15T14:30:00Z"
            }
        ],
        "total": 8
    }
}
```

### Get Conversation Messages

```http
GET /api/v1/common/chat/conversations/{conversation_id}/messages?page=1
```

### Send Message

```http
POST /api/v1/common/chat/conversations/{conversation_id}/messages
{
    "content": "Hi! Thanks for applying. When can we schedule an interview?",
    "type": "text"
}
```

Message types: "text", "file", "image"

### Start New Conversation

```http
POST /api/v1/common/chat/conversations
{
    "participant_id": "60d5ec49b4e1c8a5d8e3f1a3",
    "message": "Hi! I'd like to discuss the job opportunity."
}
```

### Upload Chat File

```http
POST /api/v1/common/chat/upload
Content-Type: multipart/form-data

file: <file>
```

Returns file URL for use in messages.

## File Management

### Upload File

```http
POST /api/v1/common/files/upload
Content-Type: multipart/form-data

file: <file>
file_type: "resume"
```

File types: "resume", "avatar", "document", "image"

### Get File Info

```http
GET /api/v1/common/files/{file_id}
```

### Delete File

```http
DELETE /api/v1/common/files/{file_id}
```

## User Profile Updates

### Update Avatar

```http
POST /api/v1/common/profile/avatar
Content-Type: multipart/form-data

avatar: <image_file>
```

### Change Password

```http
POST /api/v1/common/profile/change-password
{
    "current_password": "oldpassword123",
    "new_password": "newpassword123"
}
```

### Update Contact Info

```http
PATCH /api/v1/common/profile/contact
{
    "email": "newemail@example.com",
    "secondary_phone": "9876543211"
}
```

## System Information

### Get Categories

```http
GET /api/v1/common/categories
```

Lists job categories and subcategories.

```json
{
    "success": true,
    "data": [
        {
            "id": "60d5ec49b4e1c8a5d8e3f1a2",
            "name": "Software Development",
            "subcategories": [
                {
                    "id": "60d5ec49b4e1c8a5d8e3f1a3",
                    "name": "Backend Development"
                },
                {
                    "id": "60d5ec49b4e1c8a5d8e3f1a4",
                    "name": "Frontend Development"
                }
            ]
        }
    ]
}
```

### Get Locations

```http
GET /api/v1/common/locations?state=Maharashtra
```

Lists cities/locations, optionally filtered by state.

### Get Skills

```http
GET /api/v1/common/skills?category=Software Development
```

Lists available skills, optionally filtered by category.

### App Settings

```http
GET /api/v1/common/settings
```

Returns app configuration like maintenance mode, feature flags, etc.

## Search & Discovery

### Global Search

```http
GET /api/v1/common/search?q=python developer&type=jobs
```

Query parameters:
- `q` - Search query
- `type` - "jobs", "companies", "users" (default: "all")
- `limit` - Results per type (default: 10)

### Popular Searches

```http
GET /api/v1/common/popular-searches
```

Returns trending search terms.

### Recent Activity

```http
GET /api/v1/common/activity?page=1
```

User's recent activity feed.

## Feedback & Support

### Submit Feedback

```http
POST /api/v1/common/feedback
{
    "type": "bug_report",
    "subject": "Search not working properly",
    "description": "When I search for Python jobs, I get Java results",
    "severity": "medium"
}
```

Types: "bug_report", "feature_request", "general_feedback"
Severity: "low", "medium", "high", "critical"

### Get Help Articles

```http
GET /api/v1/common/help?category=getting_started
```

### Contact Support

```http
POST /api/v1/common/support/ticket
{
    "subject": "Payment issue",
    "description": "My payment failed but amount was deducted",
    "priority": "high"
}
```

## Analytics & Tracking

### Track Event

```http
POST /api/v1/common/analytics/track
{
    "event": "job_view",
    "properties": {
        "job_id": "60d5ec49b4e1c8a5d8e3f1a2",
        "source": "search_results"
    }
}
```

Common events:
- `job_view` - Job detail page viewed
- `application_started` - Application form opened
- `search_performed` - Search query executed
- `profile_updated` - Profile information changed

### Get User Stats

```http
GET /api/v1/common/analytics/stats
```

Personal usage statistics and insights.

## Subscription & Billing

### Get Subscription Status

```http
GET /api/v1/common/subscription
```

Shows current plan, usage, and billing info.

### Subscription Plans

```http
GET /api/v1/common/subscription/plans
```

Available subscription plans and pricing.

### Cancel Subscription

```http
POST /api/v1/common/subscription/cancel
{
    "reason": "Found alternative solution",
    "immediate": false
}
```

## Device Management

### Register Device

```http
POST /api/v1/common/devices/register
{
    "device_token": "abc123...",
    "platform": "android",
    "app_version": "1.2.3"
}
```

For push notifications.

### Update Device

```http
PATCH /api/v1/common/devices/{device_id}
{
    "device_token": "new_token...",
    "is_active": true
}
```

## Practical Notes

The common endpoints are used across all user types but some have different behavior:

**Notifications:**
- Providers get application notifications
- Seekers get status update notifications  
- Admins get system notifications
- Real-time via WebSocket but also stored in DB

**Chat System:**
- Only works between providers and seekers
- File uploads limited to 5MB
- Messages marked as read automatically when conversation opened
- No group chats or admin involvement

**File Management:**
- Files auto-deleted after 30 days if not referenced
- Image files get resized automatically
- Resume parsing happens in background
- S3 URLs expire after 24 hours

**Common Issues:**
- Search can be slow with complex queries
- File uploads sometimes timeout on slow connections
- Chat notifications can be delayed during high traffic
- Analytics events are processed asynchronously (might not show immediately)

**Rate Limits:**
- File uploads: 10 per hour
- Messages: 100 per hour
- Search: 50 per hour
- Other endpoints: 200 per hour

The analytics tracking is pretty basic - just stores events in database. No fancy dashboard or insights yet. 