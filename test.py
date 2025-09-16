# test_mongo.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

async def test_mongo():
    try:
        # Test with minimal options
        url = "mongodb+srv://royalprompts_db_user:3ieah9FIEj7EDk7a@royalprompts.dypfief.mongodb.net/royalprompts?tls=true&tlsAllowInvalidCertificates=true"
        
        client = AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000
        )
        
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client.royalprompts
        collections = await db.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_mongo())