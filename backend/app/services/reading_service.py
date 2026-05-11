from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.reading import ReadingDocument
from app.schemas.reading import (
    ReadingCreateRequest,
    ReadingResponse,
    ReadingStatsResponse,
)
from app.services.household_service import get_household_by_id


async def verify_device_ownership(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
) -> None:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    if household.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this household",
        )
    device_ids = [str(d._id) for d in household.devices]
    if device_id not in device_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found in this household",
        )


async def ingest_reading(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    payload: ReadingCreateRequest,
) -> ReadingDocument:
    await verify_device_ownership(db, household_id, device_id, user_id)
    reading = ReadingDocument(
        device_id=device_id,
        household_id=household_id,
        watts=payload.watts,
        voltage=payload.voltage,
        current=payload.current,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    await db.readings.insert_one(reading.to_dict())
    return reading


async def get_readings(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = 100,
) -> List[ReadingDocument]:
    await verify_device_ownership(db, household_id, device_id, user_id)

    query: dict = {"device_id": device_id}
    if from_ts or to_ts:
        query["timestamp"] = {}
        if from_ts:
            query["timestamp"]["$gte"] = from_ts
        if to_ts:
            query["timestamp"]["$lte"] = to_ts

    cursor = db.readings.find(query).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [ReadingDocument.from_dict(d) for d in docs]


async def get_reading_stats(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
) -> ReadingStatsResponse:
    await verify_device_ownership(db, household_id, device_id, user_id)

    now = datetime.now(timezone.utc)
    from_ts = from_ts or (now - timedelta(hours=24))
    to_ts = to_ts or now

    pipeline = [
        {
            "$match": {
                "device_id": device_id,
                "timestamp": {"$gte": from_ts, "$lte": to_ts},
            }
        },
        {
            "$group": {
                "_id": "$device_id",
                "count": {"$sum": 1},
                "avg_watts": {"$avg": "$watts"},
                "min_watts": {"$min": "$watts"},
                "max_watts": {"$max": "$watts"},
                "total_watts_sum": {"$sum": "$watts"},
            }
        },
    ]

    results = await db.readings.aggregate(pipeline).to_list(length=1)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings found for this device in the given time range",
        )

    r = results[0]
    # Convert watt-readings to kWh (assuming 1-minute intervals between readings)
    duration_hours = (to_ts - from_ts).total_seconds() / 3600
    total_kwh = (r["avg_watts"] * duration_hours) / 1000

    return ReadingStatsResponse(
        device_id=device_id,
        count=r["count"],
        avg_watts=round(r["avg_watts"], 2),
        min_watts=round(r["min_watts"], 2),
        max_watts=round(r["max_watts"], 2),
        total_kwh=round(total_kwh, 4),
        from_timestamp=from_ts,
        to_timestamp=to_ts,
    )


def format_reading_response(reading: ReadingDocument) -> ReadingResponse:
    from app.schemas.reading import ReadingResponse
    return ReadingResponse(
        id=str(reading._id),
        device_id=reading.device_id,
        household_id=reading.household_id,
        watts=reading.watts,
        voltage=reading.voltage,
        current=reading.current,
        timestamp=reading.timestamp,
    )
