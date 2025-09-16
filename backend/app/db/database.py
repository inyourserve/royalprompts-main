# # import asyncio
# # from typing import Optional
# # from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# # from beanie import init_beanie
# # from urllib.parse import urlparse
# # import certifi

# # from app.core.config import settings


# # class DatabaseManager:
# #     """Database connection and management"""
    
# #     def __init__(self):
# #         self.client: Optional[AsyncIOMotorClient] = None
# #         self.database: Optional[AsyncIOMotorDatabase] = None
# #         self.database_name: Optional[str] = None
    
# #     def _extract_database_name(self, mongodb_url: str) -> str:
# #         """Extract database name from MongoDB URL"""
# #         parsed_url = urlparse(mongodb_url)
        
# #         # If database name is in the path
# #         if parsed_url.path and parsed_url.path != '/':
# #             return parsed_url.path.lstrip('/')
        
# #         # Default database name
# #         return "royalprompts"
    
# #     async def connect(self) -> None:
# #         """Connect to MongoDB using connection string"""
# #         try:
# #             # Create client with hardcoded MongoDB URL - using same approach as Workerlly
# #             import certifi
# #             mongodb_url = "mongodb+srv://royalprompts_db_user:3ieah9FIEj7EDk7a@royalprompts.dypfief.mongodb.net/royalprompts?retryWrites=true&w=majority"
# #             self.client = AsyncIOMotorClient(mongodb_url, tlsCAFile=certifi.where())
            
# #             # Get database - hardcoded database name
# #             self.database_name = "royalprompts"
# #             self.database = self.client[self.database_name]
            
# #             # Test connection
# #             await self.client.admin.command('ping')
# #             print(f"✅ Connected to MongoDB: {self.database_name}")
# #             print(f"📍 Connection URL: {settings.MONGODB_URL.split('@')[-1] if '@' in settings.MONGODB_URL else settings.MONGODB_URL}")
            
# #         except Exception as e:
# #             print(f"❌ Failed to connect to MongoDB: {e}")
# #             print(f"🔧 Check your MongoDB URL: {settings.MONGODB_URL}")
# #             raise
    
# #     async def disconnect(self) -> None:
# #         """Disconnect from MongoDB"""
# #         if self.client:
# #             self.client.close()
# #             print("✅ Disconnected from MongoDB")
    
# #     async def init_beanie(self) -> None:
# #         """Initialize Beanie ODM with document models"""
# #         from app.models.prompt import Prompt
# #         from app.models.category import Category
# #         from app.models.favorite import Favorite
# #         from app.models.device import DeviceUser
# #         from app.models.admin import Admin
# #         from app.models.settings import AppSettings
# #         from app.models.social_link import SocialLink
        
# #         await init_beanie(
# #             database=self.database,
# #             document_models=[Prompt, Category, Favorite, DeviceUser, Admin, AppSettings, SocialLink]
# #         )
# #         print(f"✅ Beanie ODM initialized with database: {self.database_name}")
    
# #     def get_database(self) -> AsyncIOMotorDatabase:
# #         """Get database instance"""
# #         if not self.database:
# #             raise RuntimeError("Database not connected")
# #         return self.database


# # # Global database manager instance
# # db_manager = DatabaseManager()


# # async def get_database() -> AsyncIOMotorDatabase:
# #     """Dependency to get database instance"""
# #     return db_manager.get_database()


# # async def connect_to_mongo() -> None:
# #     """Connect to MongoDB and initialize Beanie"""
# #     await db_manager.connect()
# #     await db_manager.init_beanie()


# # async def close_mongo_connection() -> None:
# #     """Close MongoDB connection"""
# #     await db_manager.disconnect()
# import asyncio
# from typing import Optional
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# from beanie import init_beanie
# from urllib.parse import urlparse
# import certifi

# from app.core.config import settings


# class DatabaseManager:
#     """Database connection and management"""
    
#     def __init__(self):
#         self.client: Optional[AsyncIOMotorClient] = None
#         self.database: Optional[AsyncIOMotorDatabase] = None
#         self.database_name: Optional[str] = None
    
#     def _extract_database_name(self, mongodb_url: str) -> str:
#         """Extract database name from MongoDB URL"""
#         parsed_url = urlparse(mongodb_url)
        
#         # If database name is in the path
#         if parsed_url.path and parsed_url.path != '/':
#             return parsed_url.path.lstrip('/')
        
#         # Default database name
#         return "royalprompts"
    
#     async def connect(self) -> None:
#         """Connect to MongoDB using connection string"""
#         try:
#             # Clean MongoDB URL
#             mongodb_url = "mongodb+srv://royalprompts_db_user:3ieah9FIEj7EDk7a@royalprompts.dypfief.mongodb.net/royalprompts?retryWrites=true&w=majority"
            
#             # Correct connection options for PyMongo/Motor
#             connection_options = {
#                 'tlsCAFile': certifi.where(),
#                 'tls': True,
#                 'tlsAllowInvalidCertificates': True,
#                 'tlsAllowInvalidHostnames': True,
#                 'serverSelectionTimeoutMS': 30000,
#                 'connectTimeoutMS': 30000,
#                 'socketTimeoutMS': 30000,
#                 'maxPoolSize': 10,
#                 'minPoolSize': 1,
#                 'retryWrites': True,
#                 'w': 'majority'
#             }
            
#             self.client = AsyncIOMotorClient(mongodb_url, **connection_options)
            
#             # Get database
#             self.database_name = "royalprompts"
#             self.database = self.client[self.database_name]
            
#             # Test connection with timeout
#             await asyncio.wait_for(
#                 self.client.admin.command('ping'),
#                 timeout=30.0
#             )
            
#             print(f"✅ Connected to MongoDB: {self.database_name}")
#             print(f"📍 Connection successful to MongoDB Atlas cluster")
            
#         except asyncio.TimeoutError:
#             print(f"❌ MongoDB connection timeout - check network connectivity")
#             raise
#         except Exception as e:
#             print(f"❌ Failed to connect to MongoDB: {e}")
#             print(f"🔧 Check your MongoDB URL and network connectivity")
#             raise
    
#     async def disconnect(self) -> None:
#         """Disconnect from MongoDB"""
#         if self.client:
#             self.client.close()
#             print("✅ Disconnected from MongoDB")
    
#     async def init_beanie(self) -> None:
#         """Initialize Beanie ODM with document models"""
#         from app.models.prompt import Prompt
#         from app.models.category import Category
#         from app.models.favorite import Favorite
#         from app.models.device import DeviceUser
#         from app.models.admin import Admin
#         from app.models.settings import AppSettings
#         from app.models.social_link import SocialLink
        
#         await init_beanie(
#             database=self.database,
#             document_models=[Prompt, Category, Favorite, DeviceUser, Admin, AppSettings, SocialLink]
#         )
#         print(f"✅ Beanie ODM initialized with database: {self.database_name}")
    
#     def get_database(self) -> AsyncIOMotorDatabase:
#         """Get database instance"""
#         if not self.database:
#             raise RuntimeError("Database not connected")
#         return self.database


# # Global database manager instance
# db_manager = DatabaseManager()


# async def get_database() -> AsyncIOMotorDatabase:
#     """Dependency to get database instance"""
#     return db_manager.get_database()


# async def connect_to_mongo() -> None:
#     """Connect to MongoDB and initialize Beanie"""
#     await db_manager.connect()
#     await db_manager.init_beanie()


# async def close_mongo_connection() -> None:
#     """Close MongoDB connection"""
#     await db_manager.disconnect()

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from urllib.parse import urlparse
import certifi

from app.core.config import settings


class DatabaseManager:
    """Database connection and management"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.database_name: Optional[str] = None
    
    def _extract_database_name(self, mongodb_url: str) -> str:
        """Extract database name from MongoDB URL"""
        parsed_url = urlparse(mongodb_url)
        
        # If database name is in the path
        if parsed_url.path and parsed_url.path != '/':
            return parsed_url.path.lstrip('/')
        
        # Default database name
        return "royalprompts"
    
    async def connect(self) -> None:
        """Connect to MongoDB using connection string"""
        try:
            # Working MongoDB URL with TLS settings that bypass SSL issues
            mongodb_url = "mongodb+srv://royalprompts_db_user:3ieah9FIEj7EDk7a@royalprompts.dypfief.mongodb.net/royalprompts?tls=true&tlsAllowInvalidCertificates=true"
            
            # Minimal connection options that work
            connection_options = {
                'serverSelectionTimeoutMS': 30000,
                'connectTimeoutMS': 30000,
                'socketTimeoutMS': 30000,
                'maxPoolSize': 10,
                'minPoolSize': 1,
            }
            
            self.client = AsyncIOMotorClient(mongodb_url, **connection_options)
            
            # Get database
            self.database_name = "royalprompts"
            self.database = self.client[self.database_name]
            
            # Test connection
            await asyncio.wait_for(
                self.client.admin.command('ping'),
                timeout=30.0
            )
            
            print(f"✅ Connected to MongoDB: {self.database_name}")
            
            # Show available collections for verification
            collections = await self.database.list_collection_names()
            print(f"📁 Available collections: {collections}")
            
        except asyncio.TimeoutError:
            print(f"❌ MongoDB connection timeout - check network connectivity")
            raise
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print(f"🔧 Check your MongoDB URL and network connectivity")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("✅ Disconnected from MongoDB")
    
    async def init_beanie(self) -> None:
        """Initialize Beanie ODM with document models"""
        from app.models.prompt import Prompt
        from app.models.category import Category
        from app.models.favorite import Favorite
        from app.models.device import DeviceUser
        from app.models.admin import Admin
        from app.models.settings import AppSettings
        from app.models.social_link import SocialLink
        
        await init_beanie(
            database=self.database,
            document_models=[Prompt, Category, Favorite, DeviceUser, Admin, AppSettings, SocialLink]
        )
        print(f"✅ Beanie ODM initialized with database: {self.database_name}")
        print(f"🔧 Initialized models: Prompt, Category, Favorite, DeviceUser, Admin, AppSettings, SocialLink")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return db_manager.get_database()


async def connect_to_mongo() -> None:
    """Connect to MongoDB and initialize Beanie"""
    await db_manager.connect()
    await db_manager.init_beanie()


async def close_mongo_connection() -> None:
    """Close MongoDB connection"""
    await db_manager.disconnect()