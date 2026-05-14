from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.household import HouseholdDocument, DeviceDocument
from app.schemas.household import (
    HouseholdCreateRequest,
    HouseholdResponse,
    DeviceCreateRequest,
    DeviceResponse,
)

def _parse_household_object_id(household_id: str) -> ObjectId:
    try:
        return ObjectId(household_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid household_id format",
        )


async def get_household_by_owner(
    db: AsyncIOMotorDatabase, owner_id: str
) -> Optional[HouseholdDocument]:
    data = await db.households.find_one({"owner_id": owner_id})
    if data:
        needs_key_backfill = any(not d.get("device_key") for d in data.get("devices", []))
        household = HouseholdDocument.from_dict(data)
        if needs_key_backfill:
            await _persist_device_keys(db, household)
        return household
    return None


async def get_household_by_id(
    db: AsyncIOMotorDatabase, household_id: str
) -> Optional[HouseholdDocument]:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        )
    object_id = _parse_household_object_id(household_id)
    data = await db.households.find_one({"_id": object_id})
    if data:
        needs_key_backfill = any(not d.get("device_key") for d in data.get("devices", []))
        household = HouseholdDocument.from_dict(data)
        if needs_key_backfill:
            await _persist_device_keys(db, household)
        return household
    return None


async def _persist_device_keys(
    db: AsyncIOMotorDatabase,
    household: HouseholdDocument,
) -> None:
    await db.households.update_one(
        {"_id": household._id},
        {"$set": {"devices": [device.to_dict() for device in household.devices]}},
    )


async def create_household(
    db: AsyncIOMotorDatabase,
    payload: HouseholdCreateRequest,
    owner_id: str,
) -> HouseholdDocument:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        )
    existing = await get_household_by_owner(db, owner_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a household registered",
        )
    household = HouseholdDocument(
        owner_id=owner_id,
        name=payload.name,
        address=payload.address,
        area_sqft=payload.area_sqft,
        num_occupants=payload.num_occupants,
    )
    await db.households.insert_one(household.to_dict())
    return household


async def add_device(
    db: AsyncIOMotorDatabase,
    household_id: str,
    owner_id: str,
    payload: DeviceCreateRequest,
) -> DeviceDocument:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        )
    object_id = _parse_household_object_id(household_id)
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    if household.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this household",
        )
    device = DeviceDocument(
        name=payload.name,
        device_type=payload.device_type,
        brand=payload.brand,
        model=payload.model,
        rated_power_watts=payload.rated_power_watts,
        location=payload.location,
        is_active=payload.is_active,
    )
    await db.households.update_one(
        {"_id": object_id},
        {"$push": {"devices": device.to_dict()}},
    )
    return device


def format_device_response(device: DeviceDocument) -> DeviceResponse:
    return DeviceResponse(
        id=str(device._id),
        name=device.name,
        device_type=device.device_type,
        brand=device.brand,
        model=device.model,
        rated_power_watts=device.rated_power_watts,
        location=device.location,
        device_key=device.device_key,
        is_active=device.is_active,
        created_at=device.created_at,
    )


def format_household_response(household: HouseholdDocument) -> HouseholdResponse:
    return HouseholdResponse(
        id=str(household._id),
        owner_id=household.owner_id,
        name=household.name,
        address=household.address,
        area_sqft=household.area_sqft,
        num_occupants=household.num_occupants,
        devices=[format_device_response(d) for d in household.devices],
        created_at=household.created_at,
    )
