from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_instance = Database()


async def connect_db() -> None:
    logger.info("Connecting to MongoDB Atlas...")
    db_instance.client = AsyncIOMotorClient(settings.mongodb_uri)
    db_instance.db = db_instance.client[settings.mongodb_db_name]

    # Create indexes
    await db_instance.db.readings.create_index(
        [("household_id", 1), ("timestamp", -1)]
    )
    await db_instance.db.readings.create_index(
        [("timestamp", 1)],
        expireAfterSeconds=60 * 60 * 24 * 90  # 90 day auto-purge
    )
    await db_instance.db.users.create_index(
        [("email", 1)], unique=True
    )
    await db_instance.db.households.create_index(
        [("owner_id", 1)]
    )

    logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def close_db() -> None:
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    return db_instance.db
