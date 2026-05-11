from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
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
    KSEBSlabBreakdown,
)

# ─────────────────────────────────────────────
# KSEB Domestic LT-1 Telescopic Tariff (2025-27)
# Source: KSEB Tariff Revision Circular 2025-2027
# ─────────────────────────────────────────────
KSEB_SLABS = [
    {"limit": 50,   "rate": 3.25, "fixed": 40},
    {"limit": 100,  "rate": 4.05, "fixed": 65},
    {"limit": 150,  "rate": 5.10, "fixed": 85},
    {"limit": 200,  "rate": 6.95, "fixed": 120},
    {"limit": 250,  "rate": 8.20, "fixed": 120},
    {"limit": 300,  "rate": 6.40, "fixed": 150},
    {"limit": 350,  "rate": 7.25, "fixed": 175},
    {"limit": 400,  "rate": 7.50, "fixed": 200},
    {"limit": 500,  "rate": 7.90, "fixed": 230},
    {"limit": float("inf"), "rate": 8.80, "fixed": 260},
]
ELECTRICITY_DUTY_PCT = 0.10   # 10% on energy charge
METER_RENT           = 15.0   # ₹/month single-phase


def _kseb_bill(total_units: float) -> Tuple[float, float, float, float, List[KSEBSlabBreakdown]]:
    """
    Calculate KSEB telescopic bill.
    Returns (fixed_charge, energy_charge, electricity_duty, total_bill, slab_breakdown)
    """
    remaining  = total_units
    prev_limit = 0
    energy_charge = 0.0
    slabs: List[KSEBSlabBreakdown] = []
    fixed_charge = KSEB_SLABS[0]["fixed"]

    for slab in KSEB_SLABS:
        if remaining <= 0:
            break
        slab_size   = slab["limit"] - prev_limit
        units_in    = min(remaining, slab_size)
        cost        = round(units_in * slab["rate"], 2)
        energy_charge += cost
        fixed_charge   = slab["fixed"]   # telescopic — use highest slab's fixed charge

        label = (
            f"{prev_limit+1}–{slab['limit']} units"
            if slab["limit"] != float("inf")
            else f"Above {prev_limit} units"
        )
        slabs.append(KSEBSlabBreakdown(
            slab_label=label,
            units=round(units_in, 3),
            rate_per_unit=slab["rate"],
            slab_cost=cost,
        ))
        remaining  -= units_in
        prev_limit  = slab["limit"]

    electricity_duty = round(energy_charge * ELECTRICITY_DUTY_PCT, 2)
    total_bill = round(fixed_charge + energy_charge + electricity_duty + METER_RENT, 2)
    return fixed_charge, round(energy_charge, 2), electricity_duty, total_bill, slabs


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
                "total_wh":      {"$sum": {"$multiply": ["$watts", {"$divide": [1, 60]}]}},
                "avg_watts":     {"$avg": "$watts"},
                "peak_watts":    {"$max": "$watts"},
                "reading_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    results = await db.readings.aggregate(pipeline).to_list(length=days + 1)

    day_points = []
    total_kwh  = 0.0
    for r in results:
        kwh = round(r["total_wh"] / 1000, 4)
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
                "avg_watts":     {"$avg": "$watts"},
                "peak_watts":    {"$max": "$watts"},
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
    monthly_units = (daily.total_kwh / actual_days) * 30

    fixed, energy, duty, total, slabs = _kseb_bill(monthly_units)

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
