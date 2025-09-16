#!/usr/bin/env python3
"""
Script to clean device_user and favorites collections and re-enter fresh data
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import DatabaseManager
from app.models.device import DeviceUser, DeviceType, UserType
from app.models.favorite import Favorite
from app.models.prompt import Prompt
from app.models.category import Category
from app.services.favorite_service import FavoriteService
from app.services.prompt_service import PromptService
from app.services.device_service import DeviceService


async def clean_and_reset_data():
    """Clean collections and create fresh data"""
    
    print("🚀 Starting Clean and Reset Data Process...")
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.connect()
    await db_manager.init_beanie()
    
    try:
        # Step 1: Clean existing data
        print("\n🧹 Step 1: Cleaning existing data...")
        
        # Delete all favorites
        favorites_deleted = await Favorite.delete_all()
        print(f"   ✅ Deleted {favorites_deleted} favorites")
        
        # Delete all device users
        device_users_deleted = await DeviceUser.delete_all()
        print(f"   ✅ Deleted {device_users_deleted} device users")
        
        # Step 2: Create fresh device users
        print("\n👥 Step 2: Creating fresh device users...")
        
        device_users = []
        
        # Create 5 device users
        for i in range(5):
            device_id = str(uuid.uuid4())
            device_type = DeviceType.ANDROID if i % 2 == 0 else DeviceType.IOS
            
            device_user = DeviceUser(
                device_id=device_id,
                device_type=device_type,
                device_model=f"Model {i+1}",
                os_version=f"OS {i+1}.0",
                app_version="1.0.0",
                user_type=UserType.ANONYMOUS,
                is_active=True,
                is_blocked=False,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                total_requests=i+1,
                daily_requests=i+1,
                last_request_date=datetime.utcnow(),
                country=f"Country {i+1}",
                ip_address=f"192.168.1.{i+1}",
                user_agent=f"Mobile App {i+1}"
            )
            
            await device_user.create()
            device_users.append(device_user)
            print(f"   ✅ Created device user: {device_id} ({device_type})")
        
        # Step 3: Get existing prompts and categories
        print("\n📝 Step 3: Getting existing prompts...")
        
        from app.schemas.common import PaginationParams
        prompt_service = PromptService()
        prompts_result = await prompt_service.get_multi(PaginationParams(skip=0, limit=20))
        prompts = prompts_result.items
        
        if not prompts:
            print("   ❌ No prompts found. Please create some prompts first.")
            return
        
        print(f"   ✅ Found {len(prompts)} prompts")
        
        # Step 4: Create fresh favorites
        print("\n❤️  Step 4: Creating fresh favorites...")
        
        favorite_service = FavoriteService()
        favorites_created = 0
        
        # Each user will favorite 2-4 random prompts
        for i, user in enumerate(device_users):
            print(f"\n   👤 User {i+1}: {user.device_id}")
            
            # Select 2-4 random prompts for this user
            import random
            num_favorites = random.randint(2, 4)
            user_prompts = random.sample(prompts, min(num_favorites, len(prompts)))
            
            for prompt in user_prompts:
                try:
                    favorite = await favorite_service.add_favorite(user.device_id, str(prompt.id))
                    favorites_created += 1
                    print(f"     ✅ Favorited: {prompt.title[:40]}...")
                except Exception as e:
                    print(f"     ⚠️  Error: {str(e)}")
        
        # Step 5: Show summary
        print(f"\n📊 Step 5: Summary of fresh data...")
        
        # Count final data
        final_device_users = await DeviceUser.find_all().to_list()
        final_favorites = await Favorite.find_all().to_list()
        
        print(f"   📱 Device Users: {len(final_device_users)}")
        print(f"   ❤️  Favorites: {len(final_favorites)}")
        print(f"   📝 Prompts: {len(prompts)}")
        
        # Show favorites by user
        print(f"\n👥 Favorites by User:")
        for user in final_device_users:
            device_favorites = await favorite_service.get_device_favorites(user.device_id)
            print(f"   - {user.device_id[:8]}...: {len(device_favorites)} favorites")
        
        # Show favorites by prompt
        print(f"\n📝 Favorites by Prompt:")
        prompt_favorites = {}
        for fav in final_favorites:
            if fav.prompt_id not in prompt_favorites:
                prompt_favorites[fav.prompt_id] = 0
            prompt_favorites[fav.prompt_id] += 1
        
        for prompt_id, count in prompt_favorites.items():
            prompt = await prompt_service.get_by_id(prompt_id)
            prompt_title = prompt.title[:30] + "..." if prompt and len(prompt.title) > 30 else (prompt.title if prompt else "Unknown")
            print(f"   - {prompt_title}: {count} favorites")
        
        print(f"\n✅ Clean and reset completed successfully!")
        print(f"   - Created {len(final_device_users)} device users")
        print(f"   - Created {len(final_favorites)} favorites")
        
    except Exception as e:
        print(f"\n❌ Error during clean and reset: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()
        print("\n🔌 Disconnected from database")


if __name__ == "__main__":
    asyncio.run(clean_and_reset_data())
