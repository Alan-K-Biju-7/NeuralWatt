from datetime import datetime, timezone, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.services.household_service import get_household_by_id
from app.schemas.analytics import (
    DailyUsagePoint,
    DailyUsageResponse,
    HourlyUsagePoint,
    HourlyUsageResponse,
    UsageReportResponse,
    CostEstimateResponse,
    PeakHourPoint,
    PeakHoursResponse,
    SummaryResponse,
)
from app.services.tariff import estimate_bill, project_monthly_units


async def _authorize(db, household_id: str, user_id: str):
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


async def get_daily_usage(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    days: int = 30,
) -> DailyUsageResponse:
    await _authorize(db, household_id, user_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"device_id": device_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "total_kwh":     {"$sum": {"$ifNull": ["$energy_kwh", {"$divide": [{"$ifNull": ["$power_w", "$watts"]}, 60000]}]}},
                "avg_watts":     {"$avg": {"$ifNull": ["$power_w", "$watts"]}},
                "peak_watts":    {"$max": {"$ifNull": ["$power_w", "$watts"]}},
                "reading_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    results = await db.readings.aggregate(pipeline).to_list(length=days + 1)

    day_points = []
    total_kwh  = 0.0
    for r in results:
        kwh = round(r["total_kwh"], 4)
        total_kwh += kwh
        day_points.append(DailyUsagePoint(
            date=r["_id"],
            kwh=kwh,
            avg_watts=round(r["avg_watts"], 2),
            peak_watts=round(r["peak_watts"], 2),
            reading_count=r["reading_count"],
        ))

    from_date = since.strftime("%Y-%m-%d")
    to_date   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return DailyUsageResponse(
        device_id=device_id,
        days=day_points,
        total_kwh=round(total_kwh, 4),
        from_date=from_date,
        to_date=to_date,
    )


async def get_hourly_usage(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    days: int = 7,
) -> HourlyUsageResponse:
    await _authorize(db, household_id, user_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"device_id": device_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id":           {"$hour": "$timestamp"},
                "avg_watts":     {"$avg": {"$ifNull": ["$power_w", "$watts"]}},
                "peak_watts":    {"$max": {"$ifNull": ["$power_w", "$watts"]}},
                "reading_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    results = await db.readings.aggregate(pipeline).to_list(length=24)

    hours = [
        HourlyUsagePoint(
            hour=r["_id"],
            avg_watts=round(r["avg_watts"], 2),
            peak_watts=round(r["peak_watts"], 2),
            reading_count=r["reading_count"],
        )
        for r in results
    ]

    peak = max(hours, key=lambda h: h.avg_watts) if hours else None
    return HourlyUsageResponse(
        device_id=device_id,
        hours=hours,
        peak_hour=peak.hour if peak else 0,
        peak_hour_avg_watts=peak.avg_watts if peak else 0.0,
    )


async def get_usage_report(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    period: str = "monthly",
) -> UsageReportResponse:
    await _authorize(db, household_id, user_id)
    days   = 30 if period == "monthly" else 7
    since  = datetime.now(timezone.utc) - timedelta(days=days)

    daily  = await get_daily_usage(db, household_id, device_id, user_id, days=days)
    anomaly_count = await db.anomalies.count_documents({
        "device_id":   device_id,
        "detected_at": {"$gte": since},
    })

    peak = max(daily.days, key=lambda d: d.kwh) if daily.days else None
    low  = min(daily.days, key=lambda d: d.kwh) if daily.days else None
    avg  = round(daily.total_kwh / len(daily.days), 4) if daily.days else 0.0

    return UsageReportResponse(
        device_id=device_id,
        household_id=household_id,
        period=period,
        from_date=daily.from_date,
        to_date=daily.to_date,
        total_kwh=daily.total_kwh,
        avg_daily_kwh=avg,
        peak_day=peak.date if peak else "",
        peak_day_kwh=peak.kwh if peak else 0.0,
        low_day=low.date if low else "",
        low_day_kwh=low.kwh if low else 0.0,
        anomaly_count=anomaly_count,
        days=daily.days,
    )


async def get_cost_estimate(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    days: int = 30,
) -> CostEstimateResponse:
    await _authorize(db, household_id, user_id)
    daily = await get_daily_usage(db, household_id, device_id, user_id, days=days)

    # Pro-rate to 30-day month for KSEB slab calculation
    actual_days   = len(daily.days) or 1
    monthly_units = project_monthly_units(daily.total_kwh, actual_days)

    fixed, energy, duty, total, slabs = estimate_bill(monthly_units)

    # Per-day cost approximation for breakdown
    cost_per_kwh = (energy / monthly_units) if monthly_units > 0 else 0
    daily_breakdown = [
        {
            "date":         d.date,
            "kwh":          d.kwh,
            "approx_cost":  round(d.kwh * cost_per_kwh, 2),
        }
        for d in daily.days
    ]

    return CostEstimateResponse(
        device_id=device_id,
        from_date=daily.from_date,
        to_date=daily.to_date,
        total_kwh=daily.total_kwh,
        fixed_charge=fixed,
        energy_charge=energy,
        electricity_duty=duty,
        total_bill=total,
        slab_breakdown=slabs,
        daily_breakdown=daily_breakdown,
    )


async def get_summary(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
) -> SummaryResponse:
    await _authorize(db, household_id, user_id)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now - timedelta(days=30)

    latest = await db.readings.find_one(
        {"device_id": device_id},
        sort=[("timestamp", -1)],
    )
    pipeline = [
        {"$match": {"device_id": device_id, "timestamp": {"$gte": today_start}}},
        {
            "$group": {
                "_id": None,
                "today_kwh": {"$sum": {"$ifNull": ["$energy_kwh", {"$divide": [{"$ifNull": ["$power_w", "$watts"]}, 60000]}]}},
                "avg_power_w": {"$avg": {"$ifNull": ["$power_w", "$watts"]}},
                "peak_power_w": {"$max": {"$ifNull": ["$power_w", "$watts"]}},
                "reading_count": {"$sum": 1},
            }
        },
    ]
    rows = await db.readings.aggregate(pipeline).to_list(length=1)
    row = rows[0] if rows else {}
    anomaly_count = await db.anomalies.count_documents(
        {"device_id": device_id, "detected_at": {"$gte": month_start}}
    )
    today_kwh = round(row.get("today_kwh", 0.0), 4)
    projected = project_monthly_units(today_kwh, 1)

    return SummaryResponse(
        device_id=device_id,
        household_id=household_id,
        live_power_w=round((latest or {}).get("power_w", (latest or {}).get("watts", 0.0)), 2),
        today_kwh=today_kwh,
        avg_power_w=round(row.get("avg_power_w", 0.0), 2),
        peak_power_w=round(row.get("peak_power_w", 0.0), 2),
        projected_monthly_kwh=round(projected, 4),
        anomaly_count=anomaly_count,
        reading_count=row.get("reading_count", 0),
    )


async def get_peak_hours(
    db: AsyncIOMotorDatabase,
    household_id: str,
    device_id: str,
    user_id: str,
    days: int = 7,
    limit: int = 3,
) -> PeakHoursResponse:
    hourly = await get_hourly_usage(db, household_id, device_id, user_id, days)
    peaks = sorted(hourly.hours, key=lambda h: h.avg_watts, reverse=True)[:limit]
    return PeakHoursResponse(
        device_id=device_id,
        window_days=days,
        peaks=[
            PeakHourPoint(
                hour=h.hour,
                avg_watts=h.avg_watts,
                peak_watts=h.peak_watts,
                reading_count=h.reading_count,
            )
            for h in peaks
        ],
    )
