"""
Minimal Dependencies
Simplified for device-based and admin authentication only
"""
from app.db.database import get_database

# All authentication dependencies are now handled in:
# - app.core.device_auth (for mobile app device authentication)
# - app.core.admin_auth (for admin panel authentication)

# This file kept for potential future dependencies
