from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
client: AsyncIOMotorClient = None


async def _ensure_index(
    collection,
    keys: list[tuple[str, int]],
    *,
    unique: bool = False,
    name: str | None = None,
) -> None:
    indexes = await collection.index_information()
    for idx_name, idx_meta in indexes.items():
        if idx_meta.get("key") == keys:
            existing_unique = idx_meta.get("unique", False)
            if existing_unique == unique:
                return
            # Same key but uniqueness differs: replace to desired shape.
            logger.warning(
                "Replacing index %s on %s to unique=%s",
                idx_name,
                collection.name,
                unique,
            )
            await collection.drop_index(idx_name)
            break
    await collection.create_index(keys, unique=unique, name=name)


async def connect_db() -> None:
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    await _create_indexes(db)
    logger.info("MongoDB connected and indexes ensured ✅")


async def _create_indexes(db: AsyncIOMotorDatabase) -> None:
    await _ensure_index(
        db.users,
        [("email", 1)],
        unique=True,
        name="users_email_unique",
    )
    await _ensure_index(
        db.households,
        [("owner_id", 1)],
        unique=True,
        name="households_owner_id_unique",
    )
    await _ensure_index(
        db.readings,
        [("device_id", 1), ("timestamp", -1)],
        name="readings_device_time",
    )
    await _ensure_index(
        db.readings,
        [("household_id", 1), ("timestamp", -1)],
        name="readings_household_time",
    )
    await _ensure_index(
        db.anomalies,
        [("device_id", 1), ("detected_at", -1)],
        name="anomalies_device_detected_time",
    )
    await _ensure_index(
        db.anomalies,
        [("severity", 1)],
        name="anomalies_severity",
    )
    logger.info("MongoDB indexes created ✅")


async def close_db() -> None:
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_db() -> AsyncIOMotorDatabase:
    return client[settings.mongodb_db_name]
