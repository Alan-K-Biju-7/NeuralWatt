from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from app.db.mongodb import get_db
from app.core.security import get_current_user_id
from app.schemas.reading import (
    ReadingCreateRequest,
    ReadingResponse,
    ReadingStatsResponse,
    ReadingListResponse,
)
from app.services.reading_service import (
    ingest_reading,
    get_readings,
    get_reading_stats,
    format_reading_response,
)
from app.services.anomaly_service import detect_and_store
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/households", tags=["Readings"])


@router.post(
    "/{household_id}/devices/{device_id}/readings",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reading(
    household_id: str,
    device_id: str,
    payload: ReadingCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    reading = await ingest_reading(db, household_id, device_id, user_id, payload)

    # Run anomaly detection asynchronously — never block the response
    try:
        anomaly = await detect_and_store(
            db,
            device_id=device_id,
            household_id=household_id,
            reading_id=str(reading._id),
            watts=reading.watts,
        )
        if anomaly:
            logger.warning(
                f"Anomaly detected | device={device_id} | "
                f"{anomaly.severity.value.upper()} | {anomaly.message}"
            )
    except Exception as e:
        logger.error(f"Anomaly detection failed silently: {e}")

    return format_reading_response(reading)


@router.get(
    "/{household_id}/devices/{device_id}/readings",
    response_model=ReadingListResponse,
)
async def list_readings(
    household_id: str,
    device_id: str,
    from_ts: Optional[datetime] = Query(None, description="Start timestamp (ISO 8601)"),
    to_ts: Optional[datetime] = Query(None, description="End timestamp (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    readings = await get_readings(
        db, household_id, device_id, user_id, from_ts, to_ts, limit
    )
    return ReadingListResponse(
        device_id=device_id,
        readings=[format_reading_response(r) for r in readings],
        total=len(readings),
    )


@router.get(
    "/{household_id}/devices/{device_id}/stats",
    response_model=ReadingStatsResponse,
)
async def get_stats(
    household_id: str,
    device_id: str,
    from_ts: Optional[datetime] = Query(None, description="Start timestamp (ISO 8601)"),
    to_ts: Optional[datetime] = Query(None, description="End timestamp (ISO 8601)"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_reading_stats(
        db, household_id, device_id, user_id, from_ts, to_ts
    )
