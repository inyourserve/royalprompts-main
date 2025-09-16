# Workerlly Documentation

Workerlly is a service marketplace platform built with FastAPI. Basically connects service providers with people who need work done. Pretty standard stuff but with some nice real-time features.

## Project Structure

```
workerlly/
├── app/
│   ├── api/v1/endpoints/    # All the API routes
│   │   ├── admin/          # Admin stuff
│   │   ├── provider/       # Provider endpoints
│   │   ├── seeker/         # Seeker endpoints
│   │   └── *.py           # Shared endpoints (users, categories, etc.)
│   ├── core/              # Config and settings
│   ├── db/                # Database models
│   ├── services/          # Business logic (notification system mainly)
│   ├── templates/         # PDF invoice templates
│   ├── utils/             # Helper functions
│   └── main.py           # App entry point
├── docs/                  # This documentation
├── requirements.txt       # Python deps
├── Dockerfile            # Docker setup
└── .github/workflows/    # CI/CD
```

## What it does

- Multi-role auth (Admin/Provider/Seeker) using MSG91 OTP
- Job posting and bidding system
- Real-time location tracking when jobs are active
- Payment processing via Razorpay wallet
- Push notifications through Firebase
- Invoice generation for completed jobs
- WebSocket for real-time updates
- Review system with ratings

## Tech Stack

- **Backend**: FastAPI (Python 3.10)
- **Database**: MongoDB Atlas
- **Cache**: Redis for job notifications
- **Storage**: AWS S3 for files
- **Notifications**: Firebase Admin SDK
- **Payments**: Razorpay
- **SMS**: MSG91 for OTP
- **Deployment**: Docker + GitHub Actions

## Documentation Files

### Core Stuff
- [Database Schema](database.md) - All 21 collections with real examples
- [Services](services.md) - Notification system, analytics, caching
- [Configuration](configuration.md) - Environment variables and settings

### API Docs
- [Authentication](api/authentication.md) - MSG91 OTP integration
- [Admin Panel](api/admin.md) - Admin endpoints with permissions
- [Provider APIs](api/provider.md) - Job creation and management
- [Seeker APIs](api/seeker.md) - Job search and bidding
- [Common APIs](api/common.md) - Profile, address, utilities
- [API Flow](api/flow.md) - Request/response flows

### Deployment
- [CI/CD Pipeline](deployment/cicd.md) - GitHub Actions deployment

## Getting Started

### Local Development

```bash
git clone <repository-url>
cd workerlly
pip install -r requirements.txt
```

Setup environment variables:
```bash
# Copy the env template 
cp ".env copy" .env
# Edit .env with your actual values
```

Run it:
```bash
uvicorn app.main:app --reload
```

### Docker

```bash
docker build -t workerlly .
docker run -p 8000:8000 \
  -e SECRET_KEY=your_secret \
  -e AWS_ACCESS_KEY=your_aws_key \
  -e AWS_SECRET_ACCESS_KEY=your_aws_secret \
  -e S3_BUCKET_NAME=your_bucket \
  -e REDIS_HOST=your_redis_host \
  -e REDIS_PASSWORD=your_redis_password \
  workerlly
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Required
```bash
SECRET_KEY=your_jwt_secret_key
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

### Hardcoded (Production)
These are hardcoded in the source code:

```bash
# MSG91 OTP
MSG91_TEMPLATE_ID=672f510bd6fc0535714875e2
MSG91_AUTH_KEY=434154AnDd9jZr672f55b1P1

# Razorpay Payment Gateway  
RAZORPAY_KEY_ID=rzp_live_DBqXvgaIdpnYNz
RAZORPAY_KEY_SECRET=NgCUYG2cmhYfSJEoaamXa4Zd

# MongoDB
MONGO_URI=mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/
```

## Testing

```bash
pytest
```

## Development vs Production

**Development:**
- OTP always accepts "1234" 
- Payments in test mode
- Console logging for notifications

**Production:**
- Real MSG91 SMS delivery
- Live Razorpay transactions
- Firebase push notifications

## Business Logic Notes

- Platform takes 0% fee but adds 18% GST
- Users can be both provider and seeker
- OTP verification for job start/completion
- Real-time location tracking during jobs
- Auto wallet refunds for cancellations within 5 minutes
- Bidirectional reviews between providers and seekers

## User Roles
- **Provider**: Posts jobs, manages workers
- **Seeker**: Finds jobs, places bids, does work
- **Admin**: Manages the platform

## Deployment

### Production
- Docker Hub: `username/workerlly:latest`
- Port: 8000
- Environment: Production Digital Ocean droplet

### Test
- Docker Hub: `username/workerlly:test`  
- Port: 8001
- Environment: Test Digital Ocean droplet

## Architecture Notes

### Database
- 21 MongoDB collections
- Address snapshots in jobs for history
- Role-specific user stats
- Atomic transactions for multi-collection operations

### Notifications
- 6 event types: new_job, job_rate_update, remove_job, NEW_BID, BID_ACCEPTED, BID_REJECTED
- 4 delivery strategies: websocket_only, fcm_only, both, websocket_first_fcm_fallback  
- Redis caching with 6-minute expiry
- Basic analytics (delivery tracking only, no click/open rates)

### Security
- JWT tokens with 30-day expiry
- External OTP via MSG91 (not stored in DB)
- Pydantic validation
- Role-based admin permissions

That's pretty much it. The codebase is fairly straightforward once you understand the job lifecycle and notification system.
