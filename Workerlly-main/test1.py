import asyncio
import logging
from datetime import datetime

from app.db.models.database import motor_db

logger = logging.getLogger(__name__)


async def migrate_users_deletion_fields():
    """
    Migration script to add deletion-related fields to existing user records.
    """
    logger.info("Starting migration for user deletion fields")

    try:
        # Update all users without provider_deleted_at field
        provider_result = await motor_db.users.update_many(
            {"provider_deleted_at": {"$exists": False}},
            {"$set": {"provider_deleted_at": None}},
        )

        # Update all users without seeker_deleted_at field
        seeker_result = await motor_db.users.update_many(
            {"seeker_deleted_at": {"$exists": False}},
            {"$set": {"seeker_deleted_at": None}},
        )

        logger.info(
            f"Migration completed. Modified {provider_result.modified_count} users for provider field."
        )
        logger.info(
            f"Migration completed. Modified {seeker_result.modified_count} users for seeker field."
        )

        return {
            "provider_field_updates": provider_result.modified_count,
            "seeker_field_updates": seeker_result.modified_count,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise e


if __name__ == "__main__":
    # Run the migration when executed directly
    asyncio.run(migrate_users_deletion_fields())
