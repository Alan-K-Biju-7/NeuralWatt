from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from app.db.mongodb import get_db
from app.core.security import get_current_user_id
from app.schemas.anomaly import (
    AnomalyListResponse,
    AnomalyResponse,
    AnomalySeverity,
    BaselineResponse,
)
from app.services.anomaly_service import (
    get_anomalies,
    get_baseline,
    format_anomaly_response,
)

router = APIRouter(prefix="/households", tags=["Anomalies"])


@router.get(
    "/{household_id}/devices/{device_id}/anomalies",
    response_model=AnomalyListResponse,
)
async def list_anomalies(
    household_id: str,
    device_id: str,
    from_ts: Optional[datetime] = Query(None, description="Start timestamp (ISO 8601)"),
    to_ts: Optional[datetime] = Query(None, description="End timestamp (ISO 8601)"),
    severity: Optional[AnomalySeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    anomalies = await get_anomalies(
        db, household_id, device_id, user_id, from_ts, to_ts, severity, limit
    )
    return AnomalyListResponse(
        device_id=device_id,
        anomalies=[format_anomaly_response(a) for a in anomalies],
        total=len(anomalies),
    )


@router.get(
    "/{household_id}/devices/{device_id}/baseline",
    response_model=BaselineResponse,
)
async def get_device_baseline(
    household_id: str,
    device_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_baseline(db, household_id, device_id, user_id)
