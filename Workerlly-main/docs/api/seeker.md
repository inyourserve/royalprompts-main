# Seeker API

Job seekers use these endpoints to find jobs, apply for positions, and manage their applications.

**Base URL:** `/api/v1/seeker`  
**Authentication:** Requires `user_type: "seeker"`

## Profile Management

### Get Profile

```http
GET /api/v1/seeker/profile
```

Returns complete profile including skills, experience, and application history.

```json
{
    "success": true,
    "data": {
        "id": "60d5ec49b4e1c8a5d8e3f1a2",
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "9876543210",
        "current_location": "Mumbai, Maharashtra",
        "experience_years": 5,
        "skills": ["Python", "Django", "PostgreSQL", "React"],
        "education": [
            {
                "degree": "B.Tech Computer Science",
                "institution": "IIT Bombay",
                "year": 2019
            }
        ],
        "work_experience": [
            {
                "title": "Software Developer",
                "company": "Tech Corp",
                "duration": "2019-2022",
                "description": "Built web applications using Python and Django"
            }
        ],
        "resume_url": "https://s3.amazonaws.com/resumes/john_doe.pdf",
        "profile_completeness": 85
    }
}
```

### Update Profile

```http
PUT /api/v1/seeker/profile
{
    "current_location": "Pune, Maharashtra",
    "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "React", "Docker"],
    "expected_salary": {
        "min": 80000,
        "max": 120000,
        "currency": "INR",
        "period": "monthly"
    },
    "availability": "immediate",
    "about": "Experienced full-stack developer with 5 years in web development..."
}
```

### Upload Resume

```http
POST /api/v1/seeker/resume
Content-Type: multipart/form-data

resume: <pdf_file>
```

Automatically extracts skills and experience from resume using simple text parsing (not very sophisticated).

## Job Search

### Search Jobs

```http
GET /api/v1/seeker/jobs?location=Mumbai&skills=Python&experience=senior&page=1
```

Query parameters:
- `location` - City or state
- `skills` - Comma-separated skills
- `category` - Job category
- `experience` - "fresher", "junior", "mid", "senior"
- `job_type` - "full_time", "part_time", "contract", "freelance"
- `salary_min` - Minimum salary
- `salary_max` - Maximum salary
- `posted_since` - "today", "week", "month"
- `page` - Page number
- `limit` - Jobs per page (max 50)

Response:
```json
{
    "success": true,
    "data": {
        "jobs": [
            {
                "id": "60d5ec49b4e1c8a5d8e3f1a2",
                "title": "Senior Python Developer",
                "company": "Acme Corp",
                "location": "Mumbai, Maharashtra",
                "job_type": "full_time",
                "experience_level": "senior",
                "skills_required": ["Python", "Django", "PostgreSQL"],
                "salary_range": {
                    "min": 80000,
                    "max": 120000,
                    "currency": "INR",
                    "period": "monthly"
                },
                "posted_at": "2024-01-15T10:30:00Z",
                "application_deadline": "2024-02-15T23:59:59Z",
                "is_urgent": false,
                "match_score": 85
            }
        ],
        "total": 156,
        "page": 1,
        "pages": 4,
        "filters": {
            "locations": ["Mumbai", "Pune", "Delhi"],
            "categories": ["Software Development", "Data Science"],
            "companies": ["Acme Corp", "Tech Solutions"]
        }
    }
}
```

### Get Job Details

```http
GET /api/v1/seeker/jobs/{job_id}
```

Full job description, requirements, company info, and application instructions.

### Save Job

```http
POST /api/v1/seeker/saved-jobs
{
    "job_id": "60d5ec49b4e1c8a5d8e3f1a2",
    "notes": "Interesting role, good salary range"
}
```

### Saved Jobs

```http
GET /api/v1/seeker/saved-jobs?page=1
```

## Job Applications

### Apply for Job

```http
POST /api/v1/seeker/applications
{
    "job_id": "60d5ec49b4e1c8a5d8e3f1a2",
    "cover_letter": "I'm excited to apply for this position because...",
    "expected_salary": 100000,
    "available_from": "2024-02-01",
    "additional_info": "I have worked on similar projects at my previous company"
}
```

Uses current resume from profile. Returns application ID and confirmation.

### My Applications

```http
GET /api/v1/seeker/applications?status=pending&page=1
```

Query parameters:
- `status` - "pending", "reviewed", "shortlisted", "rejected", "hired"
- `page` - Page number

Response includes application status, applied date, and any employer feedback.

### Application Details

```http
GET /api/v1/seeker/applications/{application_id}
```

Detailed view including timeline of status changes and employer communications.

### Withdraw Application

```http
DELETE /api/v1/seeker/applications/{application_id}
```

Can only withdraw pending applications.

## Skill Assessment

### Available Tests

```http
GET /api/v1/seeker/skill-tests
```

Lists skill tests available for different technologies.

### Take Test

```http
POST /api/v1/seeker/skill-tests/{test_id}/start
```

Returns test questions and starts timer.

### Submit Test

```http
POST /api/v1/seeker/skill-tests/{test_id}/submit
{
    "answers": [
        {"question_id": "q1", "answer": "A"},
        {"question_id": "q2", "answer": "C"}
    ]
}
```

### My Test Results

```http
GET /api/v1/seeker/skill-tests/results
```

Shows scores and certification status for completed tests.

## Interview Management

### My Interviews

```http
GET /api/v1/seeker/interviews?status=scheduled
```

Upcoming and past interviews.

### Update Interview Status

```http
PATCH /api/v1/seeker/interviews/{interview_id}
{
    "status": "confirmed",
    "notes": "Looking forward to the discussion"
}
```

### Interview Feedback

```http
POST /api/v1/seeker/interviews/{interview_id}/feedback
{
    "rating": 4,
    "feedback": "Great interview experience, interviewer was helpful",
    "questions_asked": ["Technical questions about Python", "System design"]
}
```

## Company Research

### Company Details

```http
GET /api/v1/seeker/companies/{company_id}
```

Company info, culture, reviews, and active job openings.

### Company Reviews

```http
GET /api/v1/seeker/companies/{company_id}/reviews
```

Employee reviews and ratings.

### Follow Company

```http
POST /api/v1/seeker/follow-company
{
    "company_id": "60d5ec49b4e1c8a5d8e3f1a2"
}
```

Get notifications when company posts new jobs.

## Job Alerts

### Create Alert

```http
POST /api/v1/seeker/job-alerts
{
    "title": "Python Developer Jobs",
    "filters": {
        "skills": ["Python", "Django"],
        "location": "Mumbai",
        "experience": "mid",
        "salary_min": 60000
    },
    "frequency": "daily"
}
```

### My Alerts

```http
GET /api/v1/seeker/job-alerts
```

### Update Alert

```http
PUT /api/v1/seeker/job-alerts/{alert_id}
{
    "filters": {
        "location": "Mumbai, Pune",
        "salary_min": 80000
    },
    "frequency": "weekly"
}
```

## Analytics & Insights

### Application Analytics

```http
GET /api/v1/seeker/analytics/applications
```

```json
{
    "success": true,
    "data": {
        "total_applications": 45,
        "response_rate": "67%",
        "interview_rate": "23%",
        "hire_rate": "4%",
        "avg_response_time": "5 days",
        "top_skills_in_demand": ["Python", "React", "AWS"],
        "application_trends": {
            "this_week": 8,
            "last_week": 12
        }
    }
}
```

### Profile Views

```http
GET /api/v1/seeker/analytics/profile-views
```

Shows who viewed your profile and when.

### Skill Gap Analysis

```http
GET /api/v1/seeker/analytics/skill-gaps
```

Suggests skills to learn based on job market demand.

## Recommendations

### Recommended Jobs

```http
GET /api/v1/seeker/recommendations/jobs?page=1
```

AI-suggested jobs based on profile, search history, and applications.

### Recommended Courses

```http
GET /api/v1/seeker/recommendations/courses
```

Skill development courses based on career goals.

### Similar Profiles

```http
GET /api/v1/seeker/recommendations/profiles
```

Other seekers with similar backgrounds for networking.

## Networking

### My Network

```http
GET /api/v1/seeker/network
```

Connections with other users.

### Send Connection Request

```http
POST /api/v1/seeker/network/connect
{
    "user_id": "60d5ec49b4e1c8a5d8e3f1a4",
    "message": "Hi! I'd like to connect as we work in similar technologies"
}
```

### Accept/Reject Connection

```http
PATCH /api/v1/seeker/network/{connection_id}
{
    "status": "accepted"
}
```

## Practical Notes

The seeker side is pretty straightforward but has some limitations:

**Search Quality:**
- Basic keyword matching (no semantic search)
- Location matching is exact (doesn't include nearby cities)
- Match scores are simple percentage based on skill overlap

**Application System:**
- One-click apply uses your current resume
- Can't customize resume per application
- Cover letters are plain text only

**Skill Tests:**
- Limited to multiple choice questions
- Scores don't really impact job matching much
- No coding challenges or practical assessments

**Job Alerts:**
- Sometimes sends duplicate notifications
- Can't set complex filter combinations
- Email frequency can be overwhelming

**Common Issues:**
- Job recommendations aren't great (mostly shows recent posts)
- Profile completeness calculation is basic
- Some employers don't respond to applications (no follow-up system)

The analytics are helpful but not real-time - data updates once per day. Interview scheduling works but doesn't sync with external calendars. 