# Database Documentation

## Connection Setup

**Database**: MongoDB Atlas  
**Database Name**: `workerlly`  
**Connection**: `mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/`

We use both async (Motor) and sync (PyMongo) clients because some operations need sync execution:

```python
# Motor for API operations
motor_client = AsyncIOMotorClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
motor_db = motor_client.workerlly

# PyMongo for background tasks  
client = MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
db = client.workerlly
```

## Indexes

Basic indexes for performance:

```javascript
// Unique constraints
db.users.createIndex({"mobile": 1}, {unique: true})
db.categories.createIndex({"name": 1}, {unique: true})
db.cities.createIndex({"name": 1}, {unique: true})
db.admin_users.createIndex({"email": 1}, {unique: true})

// Common query patterns
db.jobs.createIndex({"status": 1, "address_snapshot.city_id": 1, "category_id": 1})
db.bids.createIndex({"job_id": 1, "user_id": 1, "status": 1})
db.transactions.createIndex({"user_id": 1, "created_at": -1})

// Geospatial for location tracking
db.active_job_locations.createIndex({"seeker_location": "2dsphere"})
```

## Collection Schemas

### Users Collection

Basic user authentication with roles:

```json
{
  "_id": ObjectId,
  "mobile": "9876543210",                    // Unique, used for login
  "roles": ["provider", "seeker"],          // Can have both roles
  "status": true,                           // Online/offline
  "created_at": ISODate,
  "provider_deleted_at": null,              // Soft delete by role
  "seeker_deleted_at": null
}
```

Authentication is mobile + OTP only. No passwords, usernames, emails in this collection.

### User Stats Collection

This is where all the actual user data lives:

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,                      // References users._id
  
  "personal_info": {
    "name": "John Doe",
    "gender": "male",
    "dob": ISODate,
    "marital_status": "single",
    "religion": "Christianity", 
    "diet": "vegetarian",
    "profile_image": "public/profiles/default.png"
  },
  
  "provider_stats": {                       // Only if user has provider role
    "city_id": ObjectId,
    "city_name": "Delhi",
    "total_jobs_posted": 25,
    "total_jobs_completed": 22,
    "total_jobs_cancelled": 2,
    "total_spent": 3300.0,
    "total_reviews": 18,
    "avg_rating": 4.5,
    "sum_ratings": 81
  },
  
  "seeker_stats": {                         // Only if user has seeker role
    "wallet_balance": 500.0,                // Razorpay wallet integration
    "city_id": ObjectId,
    "city_name": "Delhi",
    "category": {
      "category_id": ObjectId,
      "category_name": "Home Services",
      "sub_categories": [{"_id": ObjectId, "name": "House Cleaning"}]
    },
    "location": {"latitude": 28.5872, "longitude": 77.4418},
    "experience": 2,
    "user_status": {
      "current_job_id": ObjectId,           // null when free
      "current_status": "free",             // free/occupied
      "reason": null,
      "status_updated_at": ISODate
    },
    "total_jobs_done": 15,
    "total_earned": 2250.0,
    "total_hours_worked": 120,
    "total_reviews": 12,
    "avg_rating": 4.3,
    "sum_ratings": 52
  }
}
```

Why split users and user_stats? Users table stays small for auth queries, stats can grow large with all the profile data.

### Jobs Collection  

Main job data with address snapshots:

```json
{
  "_id": ObjectId,
  "task_id": "TSK123456",                   // User-facing ID
  "user_id": ObjectId,                      // Provider who created job
  "category_id": ObjectId,
  "sub_category_ids": [ObjectId],
  "title": "House Cleaning Required",
  "description": "Need someone to clean a 2BHK apartment",
  "hourly_rate": 150.0,
  "status": "pending",                      // pending → ongoing → completed/cancelled
  "assigned_to": ObjectId,                  // Seeker assigned to job
  
  "address_snapshot": {                     // Immutable copy of address
    "apartment_number": "A-123",
    "address_line1": "Sector 11, Panchkula",
    "landmark": "Near Park",
    "label": "home",
    "location": {"type": "Point", "coordinates": [76.8489, 30.6863]},
    "sub_locality": "Sector 11",
    "locality": "Panchkula", 
    "state": "Haryana",
    "pin_code": "134117",
    "country": "India",
    "city_id": ObjectId
  },
  
  "job_start_otp": 1234,                    // Generated when job accepted
  "job_done_otp": 5678,                     // Generated when job started
  "billable_hours": 2.5,                    // Calculated duration
  "total_amount": 375.0,                    // hourly_rate × billable_hours
  
  "payment_status": {
    "status": "paid",                       // pending/paid/failed
    "transaction_id": "TXN123456",
    "payment_method": "wallet",
    "paid_at": ISODate
  },
  
  "seeker_review": {
    "seeker_review_done": true,
    "seeker_review_id": ObjectId,
    "reviewed_at": ISODate
  },
  "provider_review": {
    "provider_review_done": true, 
    "provider_review_id": ObjectId,
    "reviewed_at": ISODate
  },
  
  "created_at": ISODate,
  "updated_at": ISODate
}
```

Address snapshots are important - prevents issues if user changes their address after creating a job.

### Bids Collection

Simple bidding system:

```json
{
  "_id": ObjectId,
  "job_id": ObjectId,
  "user_id": ObjectId,                      // Seeker placing bid
  "amount": 140.0,                          // Proposed hourly rate
  "status": "pending",                      // pending/accepted/rejected
  "created_at": ISODate,
  "updated_at": ISODate
}
```

When a bid is accepted, all other bids for that job are auto-rejected.

### Active Job Locations

Real-time location tracking during job execution:

```json
{
  "_id": ObjectId,
  "job_id": ObjectId,
  "provider_id": ObjectId,
  "seeker_id": ObjectId,
  "provider_location": {
    "type": "Point",
    "coordinates": [77.4418, 28.5872]      // [longitude, latitude]
  },
  "seeker_location": {
    "type": "Point", 
    "coordinates": [77.4420, 28.5874]
  },
  "status": "active",                       // active/inactive
  "created_at": ISODate,
  "last_updated": ISODate
}
```

Created when bid is accepted, updated via WebSocket, deactivated when job completes.

### Addresses Collection

User addresses with geocoding:

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "address_line1": "Sector 11, Panchkula, Haryana",
  "apartment_number": "A-123",
  "landmark": "Near Park",
  "label": "home",                          // home/work/other
  "location": {
    "type": "Point", 
    "coordinates": [76.8489, 30.6863]
  },
  "sub_locality": "Sector 11",
  "locality": "Panchkula",
  "state": "Haryana", 
  "pin_code": "134117",
  "country": "India",
  "city_id": ObjectId,
  "created_at": ISODate,
  "updated_at": ISODate,
  "deleted_at": null
}
```

Uses Google Maps API for geocoding. City lookup determines if service is available.

### Categories & Cities

Master data collections:

```json
// Categories with embedded subcategories
{
  "_id": ObjectId,
  "name": "Care Service",
  "thumbnail": "public/categories/care.png",
  "sub_categories": [
    {
      "id": ObjectId,
      "name": "Baby Sitter",
      "thumbnail": "public/subcategories/baby-sitter.png",
      "order": 1,
      "created_at": ISODate,
      "updated_at": ISODate,
      "deleted_at": null
    }
  ],
  "created_at": ISODate
}

// Cities with service availability
{
  "_id": ObjectId,
  "name": "Delhi",
  "state": "Delhi",
  "is_served": true,                        // Service availability flag
  "created_at": ISODate
}
```

### Transaction & Payment Collections

```json
// Transactions - wallet history
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "amount": 500.0,
  "transaction_type": "credit",             // credit/debit
  "description": "Wallet Recharge",
  "created_at": ISODate
}

// Payments - Razorpay integration
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "amount": 500.0,
  "razorpay_order_id": "order_ABC123",
  "razorpay_payment_id": "pay_XYZ789",
  "status": "success",                      // initiated/success/failed
  "created_at": ISODate
}
```

### Reviews Collection

Bidirectional review system:

```json
{
  "_id": ObjectId,
  "job_id": ObjectId,
  "reviewer_id": ObjectId,                  // Who wrote the review
  "reviewee_id": ObjectId,                  // Who got reviewed
  "rating": 5,                              // 1-5 stars
  "review": "Excellent work!",
  "created_at": ISODate
}
```

Both provider and seeker can review each other after job completion.

### FCM Tokens Collection

Push notification tokens:

```json
{
  "_id": ObjectId,
  "user_id": "677d222500b3156772458744",    // String, not ObjectId
  "token": "fcm_token_string",
  "app_type": "seeker",                     // provider/seeker
  "platform": "android",                   // android/ios
  "is_active": true,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

Note: user_id is stored as string here for some reason.

### Admin Collections

```json
// Admin users
{
  "_id": ObjectId,
  "name": "Admin User",
  "email": "admin@workerlly.com",
  "mobile": "9876543210",
  "password": "hashed_password",
  "roleId": ObjectId,                       // Reference to admin_roles
  "status": true,
  "mobile_verified": true,
  "created_at": ISODate
}

// Admin roles with permissions
{
  "_id": ObjectId,
  "name": "super_admin",
  "permissions": [
    {
      "resource": "users",
      "actions": ["create", "read", "update", "delete"]
    },
    {
      "resource": "jobs", 
      "actions": ["create", "read", "update", "delete"]
    }
  ],
  "created_at": ISODate
}
```

12 resources: dashboard, users, jobs, workers, providers, categories, cities, rates, faqs, roles, admins, settings.

## Transactions

We use MongoDB transactions for operations that touch multiple collections:

```python
async with session.start_transaction():
    # Create user
    result = await motor_db.users.insert_one(user_data, session=session)
    
    # Initialize user stats
    await motor_db.user_stats.insert_one(stats_data, session=session)
```

Common transaction patterns:
- User registration (users + user_stats)  
- Bid acceptance (bids + jobs + user_stats + active_job_locations)
- Job completion (jobs + transactions + user_stats + reviews)
- Payment processing (payments + transactions + user_stats)

## Collection Relationships

```
users (1) → (1) user_stats
users (1) → (many) addresses  
users (1) → (many) jobs
users (1) → (many) bids
users (1) → (many) reviews

jobs (1) → (many) bids
jobs (1) → (1) active_job_locations
jobs (1) → (many) reviews

categories (1) → (many) jobs
cities (1) → (many) addresses
cities (1) → (many) jobs (via address_snapshot)

admin_roles (1) → (many) admin_users
```

## Data Patterns

### Address Snapshots
Jobs store a complete copy of the address at creation time. This prevents issues if the user changes their address later.

### Role-based Stats  
user_stats has provider_stats and seeker_stats sections that only exist if the user has that role.

### Soft Deletes
Addresses use deleted_at field. Users use role-specific deleted_at fields (provider_deleted_at, seeker_deleted_at).

### String vs ObjectId
Most references use ObjectId, but fcm_tokens.user_id is stored as string. Inconsistent but works.

### Real-time Updates
active_job_locations is updated frequently during job execution. Other collections are more stable.

That covers the main database structure. The schema is fairly normalized with some denormalization for performance (address snapshots, embedded subcategories). 