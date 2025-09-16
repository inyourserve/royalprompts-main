#!/usr/bin/env python3
"""
Setup script to create default social links
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import DatabaseManager
from app.models.social_link import SocialLink


async def setup_social_links():
    """Setup default social links"""
    print("🔗 Setting up social links...")
    
    # Connect to database and initialize Beanie
    db_manager = DatabaseManager()
    await db_manager.connect()
    await db_manager.init_beanie()
    
    try:
        # Check existing social links
        existing_links = await SocialLink.find_all().to_list()
        print(f"   Found {len(existing_links)} existing social links")
        
        if len(existing_links) == 0:
            print("   Creating default social links...")
            default_links = SocialLink.get_default_links()
            
            for link in default_links:
                await link.create()
                print(f"   ✅ Created: {link.platform}")
            
            print(f"   ✅ Created {len(default_links)} default social links")
        else:
            print("   ✅ Social links already exist")
            
        # Show current social links
        all_links = await SocialLink.find_all().to_list()
        print(f"\n📋 Current Social Links ({len(all_links)}):")
        for link in all_links:
            status = "🟢 Active" if link.is_active else "🔴 Inactive"
            print(f"   - {link.platform}: {link.url} {status}")
            
    except Exception as e:
        print(f"❌ Error setting up social links: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()
        print("🔌 Disconnected from database")


if __name__ == "__main__":
    asyncio.run(setup_social_links())
