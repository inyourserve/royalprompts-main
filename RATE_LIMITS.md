# RoyalPrompts API Rate Limits

## Overview
Smart rate limiting system that applies different limits based on endpoint type and user role.

## Rate Limit Configuration

### 📱 Mobile API (`/api/mobile/*`)
**Limit**: 5,000 requests per minute per IP

**Use Case**: 
- Users browsing prompts
- Favoriting prompts
- Searching prompts
- Viewing categories

**Reason**: High traffic expected from mobile users actively browsing content.

---

### 🔐 Admin API (`/api/admin/*`)
**Limit**: 500 requests per minute per IP

**Use Case**:
- Uploading prompts
- Editing prompts
- Managing categories
- Viewing dashboard stats
- Managing users

**Reason**: Fewer admins, moderate CRUD operations, prevents abuse.

---

### 🔑 Authentication API (`/api/auth/*`)
**Limit**: 20 requests per minute per IP

**Use Case**:
- Admin login
- Token refresh
- Password reset

**Reason**: Strict limit to prevent brute force attacks.

---

### 🌐 Default (Other endpoints)
**Limit**: 1,000 requests per minute per IP

**Use Case**: Any endpoint not matching above categories

---

## Excluded from Rate Limiting

The following endpoints are **NOT** rate limited:
- `/health` - Health checks
- `/docs` - API documentation
- `/redoc` - ReDoc documentation  
- `/openapi.json` - OpenAPI schema
- `/` - Root endpoint

---

## Response Headers

Every API response includes rate limit information:

```http
X-RateLimit-Limit: 5000           # Max requests allowed
X-RateLimit-Remaining: 4850        # Requests remaining
X-RateLimit-Reset: 1698765432      # Unix timestamp when limit resets
```

---

## Error Response

When rate limit is exceeded:

```json
{
  "detail": "Rate limit exceeded. Max 5000 requests per 60 seconds for this endpoint."
}
```

**Status Code**: `429 Too Many Requests`

---

## Implementation Details

- **Per-IP tracking**: Each IP address has independent limits
- **Per-endpoint tracking**: Limits are tracked separately for Mobile, Admin, Auth APIs
- **Real IP detection**: Uses `X-Forwarded-For` header from Nginx
- **Memory-based**: Rate limit counters stored in application memory
- **Auto-cleanup**: Old entries automatically removed after period expires

---

## Testing Rate Limits

### Check current limit for an endpoint:
```bash
curl -I https://royalprompts.online:8443/api/mobile/prompts
```

Look for headers:
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1698765432
```

### Test rate limiting:
```bash
# This will hit the limit after 20 requests
for i in {1..25}; do
  curl https://royalprompts.online:8443/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
  echo "Request $i"
done
```

---

## Adjusting Rate Limits

To modify rate limits, edit `backend/app/core/middleware.py`:

```python
self.rate_limits = {
    "/api/mobile": {"calls": 5000, "period": 60},  # Change here
    "/api/admin": {"calls": 500, "period": 60},
    "/api/auth": {"calls": 20, "period": 60},
    "default": {"calls": 1000, "period": 60}
}
```

**Note**: Changes require container rebuild/redeploy.

---

## Production vs Development

- **Production** (`ENVIRONMENT=production`): Rate limiting **ENABLED**
- **Development** (`ENVIRONMENT=development`): Rate limiting **DISABLED**

---

## Best Practices

### For Mobile App Developers:
- Implement exponential backoff when receiving 429 errors
- Cache prompt data locally to reduce API calls
- Check `X-RateLimit-Remaining` header proactively

### For Admin Panel Developers:
- Show rate limit info in admin UI
- Warn users when approaching limit
- Implement request queuing for bulk operations

### For Users:
- 5000 requests/minute = ~83 requests/second
- Normal browsing should never hit this limit
- If you do hit it, wait 60 seconds for reset

---

## Monitoring

### On Server:
```bash
# Watch for rate limit errors in logs
docker logs -f royalprompts_backend | grep "429"

# Check current rate limit state
docker exec royalprompts_backend curl -s http://localhost:8000/api/mobile/prompts -I | grep RateLimit
```

---

## Security Notes

- Rate limits are per-IP, not per-user
- VPN/proxy users share the same IP's limit
- DDoS protection: Rate limiting alone is not sufficient
- Consider adding API keys for mobile apps in future
- Monitor for patterns of abuse

---

## Future Improvements

1. **Redis-based rate limiting**: For multi-container deployments
2. **User-based limits**: Track by user ID instead of IP
3. **API keys**: Different limits for authenticated vs anonymous users
4. **Burst allowance**: Allow short bursts above limit
5. **Rate limit bypass**: Premium users get higher limits

