# Admin API

Admin endpoints for managing users, monitoring system health, and handling platform operations.

**Base URL:** `/api/v1/admin`  
**Authentication:** Requires `user_type: "admin"`

## User Management

### List All Users

```http
GET /api/v1/admin/users?page=1&limit=20&user_type=seeker
```

Query parameters:
- `page` - Page number (default: 1)
- `limit` - Users per page (default: 20, max: 100)  
- `user_type` - Filter by type: "seeker", "provider", "admin" (optional)
- `search` - Search by name/phone/email (optional)

Response:
```json
{
    "success": true,
    "data": {
        "users": [
            {
                "id": "60d5ec49b4e1c8a5d8e3f1a2",
                "full_name": "John Doe",
                "phone": "9876543210",
                "email": "john@example.com", 
                "user_type": "seeker",
                "is_verified": true,
                "created_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-01-20T14:20:00Z"
            }
        ],
        "total": 156,
        "page": 1,
        "pages": 8
    }
}
```

### Get User Details

```http
GET /api/v1/admin/users/{user_id}
```

Returns full user profile including verification status, activity logs, and platform statistics.

### Update User Status

```http
PUT /api/v1/admin/users/{user_id}/status
{
    "is_active": false,
    "reason": "Violating platform guidelines"
}
```

Deactivates or activates user accounts. Deactivated users can't login.

### Delete User

```http
DELETE /api/v1/admin/users/{user_id}
```

Soft delete - marks user as deleted but keeps data for analytics.

## System Analytics

### Platform Statistics

```http
GET /api/v1/admin/analytics/overview
```

Response:
```json
{
    "success": true,
    "data": {
        "total_users": 1250,
        "active_users_today": 89,
        "total_jobs": 340,
        "active_jobs": 156,
        "total_applications": 2840,
        "successful_hires": 78,
        "revenue_this_month": 45000
    }
}
```

### User Growth Metrics

```http
GET /api/v1/admin/analytics/user-growth?period=7d
```

Parameters:
- `period` - "7d", "30d", "90d", "1y"

Returns daily/weekly/monthly user registration and activity data.

### Revenue Analytics

```http
GET /api/v1/admin/analytics/revenue?period=30d
```

Subscription payments, commission from successful hires, and payment method breakdown.

## Content Moderation

### Flagged Content

```http
GET /api/v1/admin/moderation/flagged?type=job_posts
```

Lists content flagged by users or automated systems:
- `type` - "job_posts", "profiles", "reviews", "messages"

### Review Flagged Item

```http
POST /api/v1/admin/moderation/review/{item_id}
{
    "action": "approve",
    "notes": "Content is appropriate"
}
```

Actions: "approve", "remove", "warn_user"

## Job Management

### All Job Posts

```http
GET /api/v1/admin/jobs?status=active&page=1
```

Parameters:
- `status` - "active", "expired", "pending", "removed"
- `category` - Filter by job category
- `location` - Filter by location

### Update Job Status

```http
PUT /api/v1/admin/jobs/{job_id}/status
{
    "status": "removed",
    "reason": "Violates posting guidelines"
}
```

### Featured Job Management

```http
POST /api/v1/admin/jobs/{job_id}/feature
{
    "featured": true,
    "duration_days": 7
}
```

Make jobs featured (appears at top of search results).

## Financial Management

### Payment Transactions

```http
GET /api/v1/admin/payments?status=completed&page=1
```

All platform transactions including subscriptions, commissions, refunds.

### Payout Management

```http
GET /api/v1/admin/payouts?status=pending
```

Manage payouts to providers from successful job completions.

### Generate Financial Reports

```http
POST /api/v1/admin/reports/financial
{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "format": "pdf"
}
```

Generates downloadable financial reports.

## System Configuration

### Platform Settings

```http
GET /api/v1/admin/settings
```

```http
PUT /api/v1/admin/settings
{
    "max_job_posts_free": 3,
    "commission_rate": 0.15,
    "featured_job_price": 500,
    "maintenance_mode": false
}
```

### Notification Templates

```http
GET /api/v1/admin/notifications/templates
```

```http
PUT /api/v1/admin/notifications/templates/{template_id}
{
    "subject": "Welcome to Workerlly!",
    "body": "Thanks for joining our platform..."
}
```

## Bulk Operations

### Send Bulk Notifications

```http
POST /api/v1/admin/bulk/notifications
{
    "user_type": "seeker",
    "title": "Platform Update",
    "message": "New features available...",
    "filters": {
        "location": "Mumbai",
        "active_since": "2024-01-01"
    }
}
```

### Export User Data

```http
POST /api/v1/admin/bulk/export
{
    "data_type": "users",
    "format": "csv",
    "filters": {
        "user_type": "provider",
        "registered_after": "2024-01-01"
    }
}
```

Returns download link for CSV/Excel export.

## Error Monitoring

### Recent Errors

```http
GET /api/v1/admin/monitoring/errors?severity=high
```

Application errors, API failures, and system issues.

### System Health

```http
GET /api/v1/admin/monitoring/health
```

```json
{
    "success": true,
    "data": {
        "database": "healthy",
        "redis": "healthy", 
        "external_apis": {
            "msg91": "healthy",
            "razorpay": "degraded",
            "firebase": "healthy"
        },
        "server_metrics": {
            "cpu_usage": "45%",
            "memory_usage": "67%",
            "disk_usage": "23%"
        }
    }
}
```

## Practical Notes

The admin panel is pretty basic - just REST APIs without a proper dashboard UI. You'd need to build a frontend or use tools like Postman for admin operations.

Some limitations:
- No role-based permissions (all admins have full access)
- Limited audit logging
- No automated alerts for critical issues
- Financial reports are basic (no advanced analytics)

Most day-to-day admin work involves:
1. Reviewing flagged content
2. Managing user complaints  
3. Monitoring payment issues
4. Handling job posting disputes

The analytics endpoints are useful but don't have real-time data - they're updated hourly.