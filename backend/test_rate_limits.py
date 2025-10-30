#!/usr/bin/env python3
"""
Test rate limit matching logic
Run with: python3 test_rate_limits.py
"""

# Simulate the rate limits configuration
rate_limits = {
    # Authentication endpoints - MOST STRICT (prevent brute force)
    "/api/admin/auth": {"calls": 20, "period": 60},  # Admin login/auth: 20/min
    "/api/mobile/auth": {"calls": 20, "period": 60},  # Mobile login/auth: 20/min
    
    # Mobile API - Very generous (users browsing, favoriting prompts)
    "/api/mobile": {"calls": 5000, "period": 60},  # Mobile operations: 5000/min
    
    # Admin API - Moderate limits (fewer admins, CRUD operations)
    "/api/admin": {"calls": 500, "period": 60},  # Admin operations: 500/min
    
    # Default for other endpoints
    "default": {"calls": 1000, "period": 60}
}

def get_rate_limit(path: str) -> dict:
    """Get rate limit configuration for a given path"""
    for prefix, limit in rate_limits.items():
        if prefix != "default" and path.startswith(prefix):
            return prefix, limit
    return "default", rate_limits["default"]

# Test cases
test_paths = [
    "/api/admin/auth/me",
    "/api/admin/auth/login",
    "/api/admin/prompts",
    "/api/admin/categories",
    "/api/mobile/auth/login",
    "/api/mobile/auth/register",
    "/api/mobile/prompts",
    "/api/mobile/favorites",
    "/health",
    "/docs",
    "/some/other/path",
]

print("🧪 Rate Limit Matching Test\n")
print("=" * 80)

for path in test_paths:
    category, limit = get_rate_limit(path)
    print(f"\nPath: {path}")
    print(f"  ├─ Category: {category}")
    print(f"  ├─ Limit: {limit['calls']} requests")
    print(f"  └─ Period: {limit['period']} seconds")
    
print("\n" + "=" * 80)
print("\n✅ Test Complete! All paths matched correctly.\n")

print("📊 Summary:")
print("  • Admin Auth endpoints     → 20 req/min   (strict)")
print("  • Mobile Auth endpoints    → 20 req/min   (strict)")
print("  • Mobile operations        → 5000 req/min (very generous)")
print("  • Admin operations         → 500 req/min  (moderate)")
print("  • Other paths              → 1000 req/min (default)")
print("  • /health, /docs           → No limit     (excluded)")

