# Mobile API Endpoints Summary

This document provides a comprehensive overview of all mobile API endpoints available in the RoyalPrompts application.

## 🔐 Authentication Endpoints

### POST `/api/mobile/auth/anonymous-login`
**Purpose**: Anonymous login for immediate app usage without registration
**Authentication**: None required
**Request Body** (Optional):
```json
{
  "device_id": "string",
  "device_type": "android|ios|web",
  "device_model": "string",
  "os_version": "string",
  "app_version": "string"
}
```
**Response**:
```json
{
  "device_token": "jwt_token",
  "expires_in": 2592000,
  "device_id": "string",
  "user_type": "anonymous",
  "rate_limits": {
    "daily_limit": 100,
    "daily_used": 0,
    "monthly_limit": 1000,
    "monthly_used": 0,
    "is_premium": false,
    "can_upgrade": false
  }
}
```

## 📂 Categories Endpoints

### GET `/api/mobile/categories`
**Purpose**: Get all active categories for mobile app
**Authentication**: None required
**Response**:
```json
[
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "is_active": true,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

## 📝 Prompts Endpoints

### GET `/api/mobile/prompts`
**Purpose**: Browse prompts with filtering and pagination
**Authentication**: Bearer token required
**Query Parameters**:
- `category` (optional): "new" | "trending" | "cinematic" | "portra"
- `search` (optional): Search term
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 50)

**Response**:
```json
{
  "items": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "content": "string",
      "category_id": "string",
      "category": {
        "id": "string",
        "name": "string"
      },
      "status": "published",
      "is_unlocked": true,
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

### GET `/api/mobile/prompts/{prompt_id}`
**Purpose**: Get detailed information about a specific prompt
**Authentication**: Bearer token required
**Response**:
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "content": "string",
  "category_id": "string",
  "category": {
    "id": "string",
    "name": "string"
  },
  "status": "published",
  "is_unlocked": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### POST `/api/mobile/prompts/{prompt_id}/unlock`
**Purpose**: Unlock a prompt for the current device
**Authentication**: Bearer token required
**Response**:
```json
{
  "message": "Prompt unlocked successfully",
  "is_unlocked": true
}
```

## ❤️ Favorites Endpoints

### GET `/api/mobile/favorites`
**Purpose**: Get all favorite prompts for the current device
**Authentication**: Bearer token required
**Response**:
```json
[
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "content": "string",
    "category_id": "string",
    "category": {
      "id": "string",
      "name": "string"
    },
    "status": "published",
    "is_unlocked": true,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

### POST `/api/mobile/favorites/{prompt_id}`
**Purpose**: Toggle favorite status for a prompt
**Authentication**: Bearer token required
**Response**:
```json
{
  "message": "Added to favorites" | "Removed from favorites",
  "is_favorited": true | false
}
```

## ⚙️ Settings Endpoints

### GET `/api/mobile/settings/app`
**Purpose**: Get public app settings for mobile app
**Authentication**: None required
**Response**:
```json
{
  "app_name": "string",
  "description": "string",
  "about_text": "string",
  "how_to_use": "string",
  "contact_email": "string"
}
```

## 🔗 Social Links Endpoints

### GET `/api/mobile/social-links/`
**Purpose**: Get active social media links for public display
**Authentication**: None required
**Response**:
```json
{
  "items": [
    {
      "platform": "string",
      "url": "string",
      "is_active": true,
      "display_order": 1
    }
  ],
  "total": 6
}
```

## 📊 Endpoint Status Summary

| Endpoint | Status | Authentication | Notes |
|----------|--------|----------------|-------|
| `POST /api/mobile/auth/anonymous-login` | ⚠️ Partial | None | Works with device info, fails without |
| `GET /api/mobile/categories` | ✅ Working | None | Returns all active categories |
| `GET /api/mobile/prompts` | ✅ Working | Bearer Token | Supports filtering and pagination |
| `GET /api/mobile/prompts/{id}` | ✅ Working | Bearer Token | Returns prompt details |
| `POST /api/mobile/prompts/{id}/unlock` | ✅ Working | Bearer Token | Unlocks prompts for device |
| `GET /api/mobile/favorites` | ✅ Working | Bearer Token | Returns device favorites |
| `POST /api/mobile/favorites/{id}` | ✅ Working | Bearer Token | Toggles favorite status |
| `GET /api/mobile/settings/app` | ✅ Working | None | Returns app settings |
| `GET /api/mobile/social-links/` | ❌ Error | None | Internal server error |

## 🔧 Issues to Fix

1. **Anonymous Login**: Fails when no device info is provided (auto-generation)
2. **Social Links**: Returns internal server error (500)

## 🚀 Usage Examples

### 1. Anonymous Login
```bash
curl -X POST "http://localhost:8000/api/mobile/auth/anonymous-login" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-device-123", "device_type": "android"}'
```

### 2. Browse Prompts
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/mobile/prompts?category=new&page=1&limit=10"
```

### 3. Get Categories
```bash
curl "http://localhost:8000/api/mobile/categories"
```

### 4. Toggle Favorite
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/mobile/favorites/PROMPT_ID"
```

## 📱 Mobile App Integration

These endpoints are designed for mobile app consumption and provide:
- Anonymous authentication for immediate usage
- Device-based user management
- Favorites and unlock functionality
- Public settings and social links
- Comprehensive prompt browsing with filtering

All endpoints return JSON responses and follow RESTful conventions.
