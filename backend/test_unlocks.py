#!/usr/bin/env python3
"""
Test script to verify unlock functionality
Run with: python3 test_unlocks.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi


async def test_unlocks():
    """Test if unlocks are being saved to database"""
    
    # Connect to MongoDB
    mongodb_url = "mongodb+srv://royalprompts_db_user:3ieah9FIEj7EDk7a@royalprompts.dypfief.mongodb.net/royalprompts?retryWrites=true&w=majority"
    
    print("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongodb_url, tlsCAFile=certifi.where())
    db = client["royalprompts"]
    
    # Test connection
    await client.admin.command('ping')
    print("✅ Connected to MongoDB")
    
    # Check unlocks collection
    unlocks_collection = db["unlocks"]
    
    # Count total unlocks
    total_unlocks = await unlocks_collection.count_documents({})
    print(f"\n📊 Total unlocks in database: {total_unlocks}")
    
    if total_unlocks > 0:
        # Show last 10 unlocks
        print("\n🔍 Last 10 unlocks:")
        cursor = unlocks_collection.find().sort("unlocked_at", -1).limit(10)
        unlocks = await cursor.to_list(length=10)
        
        for i, unlock in enumerate(unlocks, 1):
            print(f"\n{i}. Unlock ID: {unlock['_id']}")
            print(f"   Device ID: {unlock.get('device_id', 'N/A')}")
            print(f"   Prompt ID: {unlock.get('prompt_id', 'N/A')}")
            print(f"   Unlocked At: {unlock.get('unlocked_at', 'N/A')}")
    else:
        print("\n⚠️  No unlocks found in database!")
        print("\nPossible reasons:")
        print("1. No one has unlocked any prompts yet")
        print("2. Unlock endpoint is not being called")
        print("3. Unlock model not initialized properly")
        
        # Check if collection exists
        collections = await db.list_collection_names()
        print(f"\n📁 Available collections: {collections}")
        
        if "unlocks" in collections:
            print("✅ 'unlocks' collection exists but is empty")
        else:
            print("❌ 'unlocks' collection does NOT exist")
            print("   The collection will be created when first unlock is saved")
    
    # Group by device to see unlock patterns
    print("\n📊 Unlocks per device:")
    pipeline = [
        {"$group": {
            "_id": "$device_id",
            "unlock_count": {"$sum": 1}
        }},
        {"$sort": {"unlock_count": -1}},
        {"$limit": 10}
    ]
    
    cursor = unlocks_collection.aggregate(pipeline)
    devices = await cursor.to_list(length=10)
    
    if devices:
        for device in devices:
            print(f"  Device {device['_id'][:20]}...: {device['unlock_count']} unlocks")
    else:
        print("  No device data available yet")
    
    # Group by prompt to see which prompts are most unlocked
    print("\n📊 Top unlocked prompts:")
    pipeline = [
        {"$group": {
            "_id": "$prompt_id",
            "unlock_count": {"$sum": 1}
        }},
        {"$sort": {"unlock_count": -1}},
        {"$limit": 10}
    ]
    
    cursor = unlocks_collection.aggregate(pipeline)
    prompts = await cursor.to_list(length=10)
    
    if prompts:
        for prompt in prompts:
            print(f"  Prompt {prompt['_id'][:20]}...: {prompt['unlock_count']} unlocks")
    else:
        print("  No prompt data available yet")
    
    client.close()
    print("\n✅ Test completed")


if __name__ == "__main__":
    asyncio.run(test_unlocks())

