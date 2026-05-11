from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
client: AsyncIOMotorClient = None


async def connect_db() -> None:
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    await _create_indexes(db)
    logger.info("MongoDB connected and indexes ensured ✅")


async def _create_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.households.create_index("owner_id", unique=True)
    await db.readings.create_index([("device_id", 1), ("timestamp", -1)])
    await db.readings.create_index([("household_id", 1), ("timestamp", -1)])
    await db.anomalies.create_index([("device_id", 1), ("detected_at", -1)])
    await db.anomalies.create_index("severity")
    logger.info("MongoDB indexes created ✅")


async def close_db() -> None:
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_db() -> AsyncIOMotorDatabase:
    return client[settings.mongodb_db_name]
