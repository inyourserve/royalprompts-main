# Authentication

JWT-based authentication system. Nothing too fancy - just the standard login/signup/forgot password flow.

## How It Works

- User submits phone number + password or OTP
- Server validates and returns JWT token  
- Client includes token in Authorization header for protected endpoints
- Server validates token on each request

## Registration Flow

### 1. Send OTP

```http
POST /api/v1/auth/send-otp
Content-Type: application/json

{
    "phone": "9876543210"
}
```

Response:
```json
{
    "success": true,
    "message": "OTP sent successfully",
    "data": {
        "phone": "9876543210"
    }
}
```

Uses MSG91 API to send SMS. Config is hardcoded in `app/services/msg91.py`.

### 2. Verify OTP & Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "full_name": "John Doe",
    "phone": "9876543210", 
    "email": "john@example.com",
    "password": "password123",
    "user_type": "seeker",
    "otp": "123456"
}
```

Response:
```json
{
    "success": true,
    "message": "Registration successful",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user": {
            "id": "60d5ec49b4e1c8a5d8e3f1a2",
            "full_name": "John Doe",
            "phone": "9876543210",
            "email": "john@example.com",
            "user_type": "seeker",
            "is_verified": true
        }
    }
}
```

## Login Flow

### Password-based Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "phone": "9876543210",
    "password": "password123"
}
```

### OTP-based Login

First get OTP:
```http
POST /api/v1/auth/send-otp
{
    "phone": "9876543210"
}
```

Then login with OTP:
```http
POST /api/v1/auth/login-otp
{
    "phone": "9876543210",
    "otp": "123456"
}
```

Both return same JWT token format.

## Password Reset

### 1. Request Reset OTP

```http
POST /api/v1/auth/forgot-password
{
    "phone": "9876543210"
}
```

### 2. Reset with OTP

```http
POST /api/v1/auth/reset-password
{
    "phone": "9876543210",
    "otp": "123456",
    "new_password": "newpassword123"
}
```

## JWT Token Details

Tokens contain:
```json
{
    "user_id": "60d5ec49b4e1c8a5d8e3f1a2",
    "phone": "9876543210",
    "user_type": "seeker",
    "exp": 1640995200
}
```

Tokens expire in 30 days (configurable in `app/core/config.py`).

## Using Tokens

Include in Authorization header:
```http
GET /api/v1/seeker/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Protected Routes

Different endpoints need different user types:

### Seeker Routes (`/api/v1/seeker/*`)
- Requires `user_type: "seeker"`
- Examples: profile, job applications, skill tests

### Provider Routes (`/api/v1/provider/*`)  
- Requires `user_type: "provider"`
- Examples: job postings, candidate reviews

### Admin Routes (`/api/v1/admin/*`)
- Requires `user_type: "admin"`
- Examples: user management, system settings

### Common Routes (`/api/v1/common/*`)
- Any authenticated user type
- Examples: notifications, chat

## Implementation Notes

### Dependencies

Each route file uses these decorators:

```python
from app.core.security import get_current_user
from app.core.dependencies import verify_seeker, verify_provider, verify_admin

# For any authenticated user
@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    pass

# For specific user type
@router.get("/seeker-only")  
async def seeker_endpoint(current_user: dict = Depends(verify_seeker)):
    pass
```

### Token Validation

Happens in `app/core/security.py`:

1. Extract token from Authorization header
2. Decode JWT using secret key
3. Validate expiration
4. Look up user in database
5. Return user data or raise 401

### Error Responses

Invalid/missing token:
```json
{
    "detail": "Could not validate credentials"
}
```

Wrong user type:
```json
{
    "detail": "Access forbidden: Invalid user type"
}
```

## Security Notes

- JWT secret is in environment variable `SECRET_KEY`
- Passwords are hashed with bcrypt
- OTP is 6 digits, expires in 5 minutes
- No refresh token mechanism (tokens just expire)
- No logout (since JWT is stateless)

## Potential Issues

- No rate limiting on OTP requests (could be abused)
- Long token expiry (30 days) might be security risk
- No way to invalidate tokens before expiry
- OTP verification doesn't have attempt limits
- MSG91 credentials are hardcoded

Works fine for basic auth but could use improvements for production.

## OTP Service Provider
The application uses **MSG91** as the OTP service provider with the following configuration:
- Template ID: `672f510bd6fc0535714875e2`
- Auth Key: `434154AnDd9jZr672f55b1P1`
- OTP Expiry: 10 minutes (managed by MSG91)
- **Important**: OTP is NOT stored in the application database - MSG91 handles OTP generation, storage, and verification

## User Authentication Flow

### 1. Register & Send OTP
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "mobile": "9876543210",
  "roles": ["provider", "seeker"]
}
```

**Response:**
```json
{
  "message": "OTP sent to mobile"
}
```

**Implementation Details:**
- API calls MSG91 to generate and send OTP
- MSG91 stores the OTP internally for 10 minutes
- No OTP storage in Workerlly database
- OTP is sent via SMS to the provided mobile number

### 2. Verify OTP & Authenticate
```http
POST /api/v1/users/auth
Content-Type: application/json

{
  "mobile": "9876543210",
  "otp": "123456",
  "roles": ["provider", "seeker"]
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Implementation Details:**
- API sends OTP to MSG91 for verification
- If valid, user is created/updated in MongoDB
- JWT token is generated with 30-day expiry
- Existing users can add new roles (provider/seeker)

## MSG91 Integration Details

### OTP Generation Flow
```mermaid
sequenceDiagram
    participant App as Workerlly API
    participant MSG91 as MSG91 Service
    participant User as User Phone
    
    App->>MSG91: POST /api/v5/otp (Template + Mobile)
    MSG91->>MSG91: Generate & Store OTP (10 min)
    MSG91->>User: Send SMS with OTP
    MSG91-->>App: Success Response
    App-->>Client: "OTP sent to mobile"
```

### OTP Verification Flow
```mermaid
sequenceDiagram
    participant App as Workerlly API
    participant MSG91 as MSG91 Service
    participant DB as MongoDB
    
    App->>MSG91: POST /api/v5/otp/verify (Mobile + OTP)
    MSG91->>MSG91: Validate OTP
    MSG91-->>App: Validation Result
    
    alt OTP Valid
        App->>DB: Create/Update User
        App-->>Client: JWT Token
    else OTP Invalid
        App-->>Client: "Invalid OTP" Error
    end
```

### MSG91 API Endpoints Used
```javascript
// Send OTP
POST https://control.msg91.com/api/v5/otp
Parameters:
- template_id: 672f510bd6fc0535714875e2
- mobile: User's mobile number
- authkey: 434154AnDd9jZr672f55b1P1
- otp_expiry: 10 (minutes)

// Verify OTP  
POST https://control.msg91.com/api/v5/otp/verify
Parameters:
- mobile: User's mobile number
- otp: OTP entered by user
- authkey: 434154AnDd9jZr672f55b1P1
```

## Admin Authentication Flow

### 1. Admin Registration
```http
POST /api/v1/admin/register
Content-Type: application/json

{
  "email": "admin@workerlly.com",
  "password": "securepassword",
  "mobile": "9876543210",
  "name": "Admin User",
  "roles": ["admin"]
}
```

**Response:**
```json
{
  "message": "OTP sent for verification",
  "mobile": "987****3210",
  "status": "pending_verification"
}
```

### 2. Verify Admin Registration
```http
POST /api/v1/admin/verify-registration
Content-Type: application/json

{
  "mobile": "9876543210",
  "otp": "123456"
}
```

**Response:**
```json
{
  "message": "Registration completed successfully",
  "user": {
    "id": "user_id",
    "email": "admin@workerlly.com",
    "name": "Admin User",
    "mobile": "987****3210",
    "role": {
      "name": "admin",
      "permissions": ["read", "write", "delete"]
    }
  }
}
```

### 3. Admin Login
```http
POST /api/v1/admin/login
Content-Type: application/json

{
  "email": "admin@workerlly.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "email": "admin@workerlly.com",
  "mobile": "987****3210",
  "status": "pending_verification"
}
```

### 4. Verify Admin Login OTP
```http
POST /api/v1/admin/verify-login
Content-Type: application/json

{
  "email": "admin@workerlly.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "607c191e810c19729de860ea",
    "email": "admin@workerlly.com",
    "name": "John Admin",
    "mobile": "987****3210",
    "role": {
      "name": "admin",
      "permissions": ["read", "create", "update", "delete"]
    }
  }
}
```

## Authentication Security

### JWT Token Details
- **Algorithm**: HS256
- **Expiry**: 30 days (43,200 minutes)
- **Payload**: Contains user_id, mobile/email, roles/permissions
- **Secret**: From environment variable `SECRET_KEY`

### OTP Security Features
- **Expiry**: 10 minutes (enforced by MSG91)
- **Single Use**: OTP becomes invalid after successful verification
- **External Storage**: OTP never stored in application database
- **Rate Limiting**: Handled by MSG91 service

### Mock vs Production
The codebase includes mock functions for development:
```python
# Mock functions (for testing)
async def mock_send_otp(mobile: str):
    print(f"Mock OTP sent to {mobile}: 1234")
    return True

async def mock_verify_otp(mobile: str, otp: str):
    return otp == "1234"  # Always accepts "1234" in mock mode

# Production functions (MSG91 integration)
async def send_otp(mobile: str) -> bool:
    # Calls MSG91 API
    
async def verify_otp(mobile: str, otp: str) -> bool:
    # Verifies with MSG91 API
```

## Error Handling

### Common Error Responses
- `400` - Invalid OTP, email/mobile already registered
- `401` - Invalid credentials  
- `404` - User not found or not verified
- `500` - Failed to send OTP, MSG91 service error

### OTP-Specific Errors
```json
{
  "INVALID_OTP": "OTP is invalid or expired",
  "OTP_EXPIRED": "OTP has expired, please request a new one",
  "OTP_SEND_FAILED": "Failed to send OTP via SMS",
  "OTP_ALREADY_VERIFIED": "OTP has already been used",
  "MOBILE_INVALID": "Invalid mobile number format"
}
```

## Development vs Production

### Development Mode
- Uses mock OTP functions
- Always accepts OTP "1234"
- No actual SMS sent
- Useful for testing without SMS costs

### Production Mode  
- Uses actual MSG91 API
- Real SMS delivery
- Proper OTP validation
- 10-minute expiry enforced

This authentication system ensures security while providing a smooth user experience with SMS-based OTP verification handled entirely by MSG91.

## JWT Token Structure
The JWT token contains:
```json
{
  "user_id": "607c191e810c19729de860ea",
  "mobile": "9876543210",
  "roles": ["provider", "seeker"],
  "exp": 1618834123
}
```

## Token Configuration
- Algorithm: HS256
- Secret Key: Configured via `settings.SECRET_KEY`
- Expiry: Configured via `settings.ACCESS_TOKEN_EXPIRE_MINUTES`

## Role-Based Access Control
The application uses role-based access control with the following roles:
- `provider` - Can create and manage jobs
- `seeker` - Can search and apply for jobs  
- `admin` - Can access admin panel features

## Authentication Headers
All authenticated endpoints require:
```http
Authorization: Bearer <access_token>
```

## Mock Implementation
For development/testing, the application includes mock OTP functions:
- Mock OTP value: `1234` (always validates)
- `mock_send_otp()` - Prints OTP to console
- `mock_verify_otp()` - Validates against hardcoded "1234"

## Profile Endpoints

### Get Provider Profile
```http
GET /api/v1/me/provider
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "user_id",
  "mobile": "9876543210",
  "personal_info": {
    "name": "Provider Name",
    "category": {"category_id": "cat_id", "name": "Category"}
  },
  "provider_stats": {
    "total_jobs_posted": 5,
    "avg_rating": 4.5
  },
  "job_id": "current_job_id"
}
```

### Get Seeker Profile  
```http
GET /api/v1/me/seeker
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "user_id", 
  "mobile": "9876543210",
  "personal_info": {
    "name": "Seeker Name",
    "category": {"category_id": "cat_id", "name": "Category"}
  },
  "seeker_stats": {
    "total_jobs_applied": 10,
    "avg_rating": 4.2
  }
}
```

## Role Deletion Endpoints

### Delete Provider Role
```http
POST /api/v1/delete/provider
Authorization: Bearer <token>
```

### Delete Seeker Role
```http  
POST /api/v1/delete/seeker
Authorization: Bearer <token>
```

## Error Responses
- `400` - Invalid OTP, email/mobile already registered
- `401` - Invalid credentials  
- `404` - User not found or not verified
- `500` - Failed to send OTP, server error 