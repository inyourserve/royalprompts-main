# Provider API

Endpoints for job providers (employers) to post jobs, manage applications, and handle hiring.

**Base URL:** `/api/v1/provider`  
**Authentication:** Requires `user_type: "provider"`

## Profile Management

### Get Profile

```http
GET /api/v1/provider/profile
```

Returns complete provider profile including company info, verification status, and statistics.

```json
{
    "success": true,
    "data": {
        "id": "60d5ec49b4e1c8a5d8e3f1a2",
        "full_name": "Acme Corp",
        "email": "hr@acme.com",
        "phone": "9876543210",
        "company_info": {
            "company_name": "Acme Corporation",
            "industry": "Technology",
            "company_size": "51-200",
            "location": "Mumbai, Maharashtra"
        },
        "verification_status": "verified",
        "stats": {
            "jobs_posted": 25,
            "active_jobs": 8,
            "successful_hires": 15,
            "avg_response_time": "2 hours"
        }
    }
}
```

### Update Profile

```http
PUT /api/v1/provider/profile
{
    "company_name": "Acme Corp Pvt Ltd",
    "industry": "Software Development",
    "company_size": "201-500",
    "location": "Mumbai, Maharashtra",
    "description": "Leading software development company..."
}
```

## Job Posting

### Create Job

```http
POST /api/v1/provider/jobs
{
    "title": "Senior Python Developer",
    "description": "We're looking for an experienced Python developer...",
    "category": "Software Development",
    "subcategory": "Backend Development",
    "location": "Mumbai, Maharashtra",
    "job_type": "full_time",
    "experience_level": "senior",
    "skills_required": ["Python", "Django", "PostgreSQL", "Redis"],
    "salary_range": {
        "min": 80000,
        "max": 120000,
        "currency": "INR",
        "period": "monthly"
    },
    "benefits": ["Health Insurance", "Work from Home", "Flexible Hours"],
    "application_deadline": "2024-02-15T23:59:59Z",
    "is_urgent": false
}
```

Response includes job ID and posting confirmation.

### My Job Posts

```http
GET /api/v1/provider/jobs?status=active&page=1&limit=10
```

Query parameters:
- `status` - "active", "paused", "closed", "expired"
- `category` - Filter by job category
- `page` - Page number
- `limit` - Jobs per page

### Update Job

```http
PUT /api/v1/provider/jobs/{job_id}
{
    "title": "Updated Job Title",
    "description": "Updated description...",
    "salary_range": {
        "min": 90000,
        "max": 130000
    }
}
```

### Pause/Resume Job

```http
PATCH /api/v1/provider/jobs/{job_id}/status
{
    "status": "paused"
}
```

Status options: "active", "paused", "closed"

## Application Management

### Get Applications

```http
GET /api/v1/provider/applications?job_id={job_id}&status=pending
```

Query parameters:
- `job_id` - Filter by specific job (optional)
- `status` - "pending", "reviewed", "shortlisted", "rejected", "hired"
- `page` - Page number
- `limit` - Applications per page

Response:
```json
{
    "success": true,
    "data": {
        "applications": [
            {
                "id": "60d5ec49b4e1c8a5d8e3f1a3",
                "job_title": "Senior Python Developer",
                "applicant": {
                    "id": "60d5ec49b4e1c8a5d8e3f1a4",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "experience_years": 5,
                    "current_location": "Mumbai",
                    "skills": ["Python", "Django", "PostgreSQL"]
                },
                "status": "pending",
                "applied_at": "2024-01-15T10:30:00Z",
                "cover_letter": "I'm excited to apply for this position...",
                "resume_url": "https://s3.amazonaws.com/resumes/john_doe.pdf"
            }
        ],
        "total": 45,
        "page": 1,
        "pages": 5
    }
}
```

### Update Application Status

```http
PATCH /api/v1/provider/applications/{application_id}
{
    "status": "shortlisted",
    "notes": "Good experience, move to interview round"
}
```

### Bulk Update Applications

```http
POST /api/v1/provider/applications/bulk-update
{
    "application_ids": ["id1", "id2", "id3"],
    "status": "rejected",
    "notes": "Requirements not met"
}
```

### Send Message to Applicant

```http
POST /api/v1/provider/applications/{application_id}/message
{
    "message": "Thanks for applying! We'd like to schedule an interview.",
    "type": "interview_request"
}
```

## Candidate Search

### Search Candidates

```http
GET /api/v1/provider/search-candidates?skills=Python,Django&location=Mumbai&experience_min=3
```

Query parameters:
- `skills` - Comma-separated skills
- `location` - City/state
- `experience_min` - Minimum years experience
- `experience_max` - Maximum years experience
- `availability` - "immediate", "within_month", "flexible"

### Save Candidate

```http
POST /api/v1/provider/saved-candidates
{
    "candidate_id": "60d5ec49b4e1c8a5d8e3f1a4",
    "notes": "Strong Django experience, good fit for our team"
}
```

### Contact Candidate

```http
POST /api/v1/provider/contact-candidate
{
    "candidate_id": "60d5ec49b4e1c8a5d8e3f1a4",
    "message": "Hi! We have an opening that matches your skills...",
    "job_id": "60d5ec49b4e1c8a5d8e3f1a2"
}
```

## Analytics & Reports

### Dashboard Stats

```http
GET /api/v1/provider/dashboard
```

```json
{
    "success": true,
    "data": {
        "active_jobs": 8,
        "total_applications": 156,
        "pending_reviews": 23,
        "successful_hires": 15,
        "response_rate": "85%",
        "avg_time_to_hire": "12 days",
        "top_performing_job": {
            "title": "Senior Python Developer",
            "applications": 45
        }
    }
}
```

### Application Analytics

```http
GET /api/v1/provider/analytics/applications?period=30d
```

Returns application trends, source breakdown, and conversion rates.

### Job Performance

```http
GET /api/v1/provider/analytics/jobs/{job_id}
```

Detailed analytics for specific job including view count, application rate, and demographics.

## Interview Management

### Schedule Interview

```http
POST /api/v1/provider/interviews
{
    "application_id": "60d5ec49b4e1c8a5d8e3f1a3",
    "interview_type": "phone",
    "scheduled_at": "2024-01-20T14:00:00Z",
    "duration_minutes": 60,
    "interview_link": "https://meet.google.com/abc-def-ghi",
    "notes": "Technical discussion about Python experience"
}
```

### My Interviews

```http
GET /api/v1/provider/interviews?status=scheduled&date=2024-01-20
```

### Update Interview

```http
PATCH /api/v1/provider/interviews/{interview_id}
{
    "status": "completed",
    "feedback": "Strong technical skills, good communication",
    "rating": 4,
    "next_steps": "Move to final round"
}
```

## Subscription & Billing

### Current Plan

```http
GET /api/v1/provider/subscription
```

Shows current plan details, usage limits, and billing information.

### Upgrade Plan

```http
POST /api/v1/provider/subscription/upgrade
{
    "plan_id": "premium",
    "billing_cycle": "monthly"
}
```

### Usage Stats

```http
GET /api/v1/provider/usage
```

Current month's usage against plan limits (job posts, candidate searches, etc.).

## Team Management

### Team Members

```http
GET /api/v1/provider/team
```

### Add Team Member

```http
POST /api/v1/provider/team
{
    "email": "colleague@acme.com",
    "role": "recruiter",
    "permissions": ["view_applications", "update_application_status"]
}
```

### Update Team Member

```http
PATCH /api/v1/provider/team/{member_id}
{
    "role": "senior_recruiter",
    "permissions": ["view_applications", "update_application_status", "schedule_interviews"]
}
```

## Notifications

### Notification Settings

```http
GET /api/v1/provider/notification-settings
```

```http
PUT /api/v1/provider/notification-settings
{
    "email_notifications": {
        "new_applications": true,
        "application_status_updates": true,
        "job_expiry_reminders": true
    },
    "sms_notifications": {
        "urgent_applications": true,
        "interview_reminders": true
    }
}
```

## Practical Notes

The provider API is pretty comprehensive but has some quirks:

**Job Posting Limits:**
- Free tier: 3 jobs per month
- Premium: 25 jobs per month  
- Enterprise: Unlimited

**Application Management:**
- No built-in ATS integration (you'd need to export data)
- Bulk operations are limited to 50 items at once
- File uploads go to S3 but URLs expire after 24 hours

**Search Limitations:**
- Candidate search is basic (no advanced filters)
- No saved search functionality
- Results limited to 100 candidates per search

**Common Issues:**
- Application status updates don't always trigger notifications
- File uploads can be slow (no progress tracking)
- Subscription billing is handled by Razorpay but no webhooks for failed payments

The interview scheduling is pretty basic - just stores data, doesn't integrate with calendars. Most providers end up using external tools for actual interview management. 