import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.anomaly import AnomalyDocument
from app.schemas.anomaly import AnomalySeverity, AnomalyResponse, BaselineResponse
from app.services.household_service import get_household_by_id
import logging

logger = logging.getLogger(__name__)

Z_LOW    = 2.0
Z_MEDIUM = 3.0
Z_HIGH   = 4.0


def _classify_severity(z_score: float, deviation_pct: float) -> AnomalySeverity:
    abs_z = abs(z_score)
    abs_dev = abs(deviation_pct)

    # Keep z-score as the primary signal, but promote severity when
    # percent deviation is extremely high (z-score can be dampened by
    # previously spiky baselines).
    if abs_z >= Z_HIGH or abs_dev >= 300:
        return AnomalySeverity.HIGH
    elif abs_z >= Z_MEDIUM or abs_dev >= 150:
        return AnomalySeverity.MEDIUM
    return AnomalySeverity.LOW


def _build_message(watts: float, expected: float, deviation_pct: float, severity: AnomalySeverity) -> str:
    direction = "above" if watts > expected else "below"
    return (
        f"{severity.value.upper()} anomaly: {watts:.1f}W is "
        f"{abs(deviation_pct):.1f}% {direction} expected {expected:.1f}W"
    )


async def _compute_baseline(
    db: AsyncIOMotorDatabase,
    device_id: str,
    lookback_hours: int = 72,
) -> Tuple[float, float, int]:
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    pipeline = [
        {"$match": {"device_id": device_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": None,
                "avg": {"$avg": "$watts"},
                "count": {"$sum": 1},
                "sq_sum": {"$sum": {"$multiply": ["$watts", "$watts"]}},
                "sum": {"$sum": "$watts"},
            }
        },
    ]
    results = await db.readings.aggregate(pipeline).to_list(length=1)
    if not results or results[0]["count"] < 3:
        return 0.0, 0.0, 0
    r = results[0]
    mean = r["avg"]
    count = r["count"]
    variance = (r["sq_sum"] / count) - (mean ** 2)
    std_dev = math.sqrt(max(variance, 0))
    return mean, std_dev, count


async def detect_and_store(
    db: AsyncIOMotorDatabase,
    device_id: str,
    household_id: str,
    reading_id: str,
    watts: float,
) -> Optional[AnomalyDocument]:
    mean, std_dev, count = await _compute_baseline(db, device_id)
    if count < 3 or std_dev == 0:
        return None

    z_score = (watts - mean) / std_dev
    if abs(z_score) < Z_LOW:
        return None

    deviation_pct = ((watts - mean) / mean) * 100
    severity = _classify_severity(z_score, deviation_pct)
    message = _build_message(watts, mean, deviation_pct, severity)

    anomaly = AnomalyDocument(
        device_id=device_id,
        household_id=household_id,
        reading_id=reading_id,
        watts=watts,
        expected_watts=round(mean, 2),
        deviation_pct=round(deviation_pct, 2),
        severity=severity,
        message=message,
    )
    await db.anomalies.insert_one(anomaly.to_dict())

    # Dispatch alerts — import here to avoid circular imports
    try:
        from app.services.alert_config_service import get_configs_for_device
        from app.services.notification_service import dispatch_alerts
        configs = await get_configs_for_device(db, device_id)
        if configs:
            await dispatch_alerts(anomaly, configs)
    except Exception as e:
        logger.error(f"Alert dispatch failed silently: {e}")

    return anomaly


async def get_anomalies(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    from_ts=None,
    to_ts=None,
    severity=None,
    limit: int = 50,
) -> List[AnomalyDocument]:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    query: dict = {"device_id": device_id}
    if severity:
        query["severity"] = severity
    if from_ts or to_ts:
        query["detected_at"] = {}
        if from_ts:
            query["detected_at"]["$gte"] = from_ts
        if to_ts:
            query["detected_at"]["$lte"] = to_ts

    cursor = db.anomalies.find(query).sort("detected_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [AnomalyDocument.from_dict(d) for d in docs]


async def get_baseline(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
) -> BaselineResponse:
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    mean, std_dev, count = await _compute_baseline(db, device_id)
    if count < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough readings to compute baseline (need at least 3)",
        )
    return BaselineResponse(
        device_id=device_id,
        avg_watts=round(mean, 2),
        std_dev=round(std_dev, 2),
        sample_count=count,
        computed_at=datetime.now(timezone.utc),
    )


def format_anomaly_response(anomaly: AnomalyDocument) -> AnomalyResponse:
    return AnomalyResponse(
        id=str(anomaly._id),
        device_id=anomaly.device_id,
        household_id=anomaly.household_id,
        reading_id=anomaly.reading_id,
        watts=anomaly.watts,
        expected_watts=anomaly.expected_watts,
        deviation_pct=anomaly.deviation_pct,
        severity=anomaly.severity,
        detected_at=anomaly.detected_at,
        message=anomaly.message,
    )
