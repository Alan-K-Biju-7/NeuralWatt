from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.alert_config import AlertConfigDocument
from app.schemas.alert_config import (
    AlertConfigCreateRequest,
    AlertConfigUpdateRequest,
    AlertConfigResponse,
)
from app.services.household_service import get_household_by_id


async def create_alert_config(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    payload: AlertConfigCreateRequest,
) -> AlertConfigDocument:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # One config per device — upsert pattern
    existing = await db.alert_configs.find_one({"device_id": device_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert config already exists for this device. Use PATCH to update.",
        )

    config = AlertConfigDocument(
        device_id=device_id,
        household_id=household_id,
        owner_id=user_id,
        severity_threshold=payload.severity_threshold,
        email_enabled=payload.email_enabled,
        email_address=str(payload.email_address) if payload.email_address else None,
        webhook_enabled=payload.webhook_enabled,
        webhook_url=str(payload.webhook_url) if payload.webhook_url else None,
    )
    await db.alert_configs.insert_one(config.to_dict())
    return config


async def get_alert_config(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
) -> AlertConfigDocument:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    doc = await db.alert_configs.find_one({"device_id": device_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert config found for this device",
        )
    return AlertConfigDocument.from_dict(doc)


async def update_alert_config(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    payload: AlertConfigUpdateRequest,
) -> AlertConfigDocument:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    updates = payload.model_dump(exclude_none=True)
    if "email_address" in updates:
        updates["email_address"] = str(updates["email_address"])
    if "webhook_url" in updates:
        updates["webhook_url"] = str(updates["webhook_url"])
    if "severity_threshold" in updates:
        updates["severity_threshold"] = updates["severity_threshold"].value

    updates["updated_at"] = datetime.now(timezone.utc)

    result = await db.alert_configs.find_one_and_update(
        {"device_id": device_id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert config found for this device",
        )
    return AlertConfigDocument.from_dict(result)


async def delete_alert_config(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
) -> None:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.alert_configs.delete_one({"device_id": device_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert config found for this device",
        )


async def get_configs_for_device(
    db: AsyncIOMotorDatabase,
    device_id: str,
) -> List[AlertConfigDocument]:
    """Internal use — called by anomaly service to fetch configs before dispatching alerts."""
    cursor = db.alert_configs.find({"device_id": device_id})
    docs = await cursor.to_list(length=10)
    return [AlertConfigDocument.from_dict(d) for d in docs]


def format_alert_config_response(config: AlertConfigDocument) -> AlertConfigResponse:
    return AlertConfigResponse(
        id=str(config._id),
        device_id=config.device_id,
        household_id=config.household_id,
        severity_threshold=config.severity_threshold,
        email_enabled=config.email_enabled,
        email_address=config.email_address,
        webhook_enabled=config.webhook_enabled,
        webhook_url=config.webhook_url,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )
