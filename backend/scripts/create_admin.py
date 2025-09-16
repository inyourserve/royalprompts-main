#!/usr/bin/env python3
"""
Script to create initial admin user
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.database import DatabaseManager
from app.services.admin_service import AdminService
from app.models.admin import AdminRole


async def create_admin():
    """Create initial admin user"""
    try:
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.connect()
        await db_manager.init_beanie()
        
        admin_service = AdminService()
        
        # Check if any admin exists
        existing_admin = await admin_service.repository.find_one({})
        if existing_admin:
            print("❌ Admin user already exists")
            return
        
        # Create super admin
        email = "admin@royalprompts.com"
        username = "admin"
        password = "admin123"  # Change this in production
        full_name = "Super Admin"
        
        admin = await admin_service.create_admin(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            role=AdminRole.SUPER_ADMIN
        )
        
        print("✅ Super admin created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"🔑 Password: {password}")
        print("⚠️  Please change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(create_admin())
