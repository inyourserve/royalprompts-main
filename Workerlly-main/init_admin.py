# scripts/init_admin.py

from datetime import datetime

from passlib.context import CryptContext

from app.db.models.database import motor_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define all admin resources and their actions
ADMIN_RESOURCES = {
    "dashboard": ["read"],
    "users": ["create", "read", "update", "delete"],
    "jobs": ["create", "read", "update", "delete"],
    "workers": ["create", "read", "update", "delete"],
    "categories": ["create", "read", "update", "delete"],
    "cities": ["create", "read", "update", "delete"],
    "rates": ["create", "read", "update", "delete"],
    "faqs": ["create", "read", "update", "delete"],
    "roles": ["create", "read", "update", "delete"],
    "permissions": ["create", "read", "update", "delete"],
    "settings": ["read", "update"],
}

# Define default roles with their permissions
DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "description": "Full access to all features",
        "permissions": [
            {"resource": resource, "actions": actions}
            for resource, actions in ADMIN_RESOURCES.items()
        ],
    },
    {
        "name": "admin",
        "description": "Administrative access with some restrictions",
        "permissions": [
            {"resource": "dashboard", "actions": ["read"]},
            {"resource": "users", "actions": ["read", "create", "update"]},
            {"resource": "jobs", "actions": ["create", "read", "update", "delete"]},
            {"resource": "workers", "actions": ["read", "create", "update"]},
            {
                "resource": "categories",
                "actions": ["create", "read", "update", "delete"],
            },
            {"resource": "cities", "actions": ["create", "read", "update", "delete"]},
            {"resource": "rates", "actions": ["create", "read", "update", "delete"]},
            {"resource": "faqs", "actions": ["create", "read", "update", "delete"]},
        ],
    },
    {
        "name": "moderator",
        "description": "Content moderation access",
        "permissions": [
            {"resource": "dashboard", "actions": ["read"]},
            {"resource": "users", "actions": ["read"]},
            {"resource": "jobs", "actions": ["read", "update"]},
            {"resource": "workers", "actions": ["read", "update"]},
            {"resource": "categories", "actions": ["read", "create", "update"]},
            {"resource": "cities", "actions": ["read"]},
            {"resource": "rates", "actions": ["read"]},
        ],
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "permissions": [
            {"resource": resource, "actions": ["read"]}
            for resource in ADMIN_RESOURCES.keys()
        ],
    },
]


async def init_collections():
    """Initialize collections and create indexes"""
    try:
        collections = await motor_db.list_collection_names()
        required_collections = ["admin_users", "admin_roles"]

        # Create collections if they don't exist
        for collection in required_collections:
            if collection not in collections:
                await motor_db.create_collection(collection)

        # Create indexes
        await motor_db.admin_users.create_index("email", unique=True)
        await motor_db.admin_users.create_index("mobile", unique=True)
        await motor_db.admin_roles.create_index("name", unique=True)

        print("Collections and indexes created successfully!")
        return True
    except Exception as e:
        print(f"Error creating collections and indexes: {str(e)}")
        return False


async def init_roles():
    """Initialize default roles with permissions"""
    try:
        for role in DEFAULT_ROLES:
            existing_role = await motor_db.admin_roles.find_one({"name": role["name"]})
            if not existing_role:
                await motor_db.admin_roles.insert_one(
                    {
                        **role,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
        print("Roles initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing roles: {str(e)}")
        return False


async def create_default_admin():
    """Create default super admin user"""
    try:
        # Get super_admin role
        super_admin_role = await motor_db.admin_roles.find_one({"name": "super_admin"})
        if not super_admin_role:
            print("Super admin role not found!")
            return False

        default_admin = await motor_db.admin_users.find_one(
            {"email": "admin@example.com"}
        )
        if not default_admin:
            super_admin = {
                "email": "admin@example.com",
                "password": pwd_context.hash("admin123"),
                "name": "Super Admin",
                "roleId": super_admin_role["_id"],
                "status": True,
                "mobile": "1234567890",
                "mobile_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
            }
            await motor_db.admin_users.insert_one(super_admin)
            print("Default admin user created successfully!")
        return True
    except Exception as e:
        print(f"Error creating default admin: {str(e)}")
        return False


async def init_admin_system():
    """Main initialization function"""
    try:
        # Initialize collections and indexes
        if not await init_collections():
            return False

        # Initialize roles with permissions
        if not await init_roles():
            return False

        # Create default admin
        if not await create_default_admin():
            return False

        print("Admin system initialized successfully!")
        return True

    except Exception as e:
        print(f"Error in admin system initialization: {str(e)}")
        return False


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_admin_system())
