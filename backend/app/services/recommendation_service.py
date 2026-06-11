from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.household_service import get_household_by_id
from app.services.tariff import estimate_bill


KSEB_PEAK_HOURS = {18, 19, 20, 21, 22}


def _estimate_energy_kwh(frame: pd.DataFrame) -> pd.Series:
    power_source = (
        frame["power_w"]
        if "power_w" in frame.columns
        else pd.Series(0.0, index=frame.index)
    )
    power_w = pd.to_numeric(power_source, errors="coerce").fillna(0.0)
    power_w = power_w.clip(lower=0)
    deltas = frame["timestamp"].diff().dt.total_seconds().div(3600)
    median_delta = deltas[(deltas > 0) & (deltas < 1)].median()
    if pd.isna(median_delta):
        median_delta = 5 / 3600
    deltas = deltas.fillna(median_delta).clip(lower=0, upper=1)
    return power_w * deltas / 1000


def summarize_readings(readings: pd.DataFrame) -> dict:
    if readings.empty:
        return {
            "total_kwh": 0.0,
            "peak_kwh": 0.0,
            "average_power_w": 0.0,
            "max_power_w": 0.0,
            "reading_count": 0,
            "estimated_daily_cost": 0.0,
        }

    frame = readings.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")
    if frame.empty:
        return {
            "total_kwh": 0.0,
            "peak_kwh": 0.0,
            "average_power_w": 0.0,
            "max_power_w": 0.0,
            "reading_count": 0,
            "estimated_daily_cost": 0.0,
        }
    if "power_w" not in frame.columns and "watts" in frame.columns:
        frame["power_w"] = frame["watts"]
    power_source = (
        frame["power_w"]
        if "power_w" in frame.columns
        else pd.Series(0.0, index=frame.index)
    )
    frame["power_w"] = pd.to_numeric(power_source, errors="coerce").fillna(0)

    if "energy_kwh" in frame.columns:
        energy = pd.to_numeric(frame["energy_kwh"], errors="coerce").fillna(0.0)
        if energy.sum() <= 0:
            energy = _estimate_energy_kwh(frame)
    else:
        energy = _estimate_energy_kwh(frame)
    frame["energy_kwh"] = energy.clip(lower=0)
    frame["local_hour"] = frame["timestamp"].dt.tz_convert("Asia/Kolkata").dt.hour

    total_kwh = float(frame["energy_kwh"].sum())
    monthly_units = total_kwh * 30
    _, _, _, monthly_bill, _ = estimate_bill(monthly_units)

    return {
        "total_kwh": round(total_kwh, 4),
        "peak_kwh": round(
            float(frame.loc[frame["local_hour"].isin(KSEB_PEAK_HOURS), "energy_kwh"].sum()),
            4,
        ),
        "average_power_w": round(float(frame["power_w"].mean()), 2),
        "max_power_w": round(float(frame["power_w"].max()), 2),
        "reading_count": int(len(frame)),
        "estimated_daily_cost": round(monthly_bill / 30, 2),
    }


def evaluate_rules(summary: dict) -> list[dict]:
    recommendations: list[dict] = []
    total_kwh = summary["total_kwh"]
    peak_kwh = summary["peak_kwh"]
    peak_fraction = peak_kwh / total_kwh if total_kwh else 0

    if total_kwh > 8:
        recommendations.append(
            {
                "id": "high_daily_energy",
                "title": "High household energy use today",
                "message": "Today's usage is above 8 kWh. Shift deferrable loads and review high-power appliances.",
                "severity": "high",
                "savings_hint": "Possible 10-15% daily energy reduction",
            }
        )

    if peak_fraction > 0.35:
        recommendations.append(
            {
                "id": "peak_hour_shift",
                "title": "Peak-hour load is concentrated",
                "message": "A large share of energy is used between 6 PM and 10 PM. Move washing or induction cooking prep outside peak hours where practical.",
                "severity": "medium",
                "savings_hint": "Improves peak demand and billing predictability",
            }
        )

    if summary["max_power_w"] > 1800:
        recommendations.append(
            {
                "id": "high_power_spike",
                "title": "High-power spike detected",
                "message": "One or more readings crossed 1.8 kW. Avoid running kettle, iron, washing machine heater, and induction together.",
                "severity": "medium",
                "savings_hint": "Reduces overload risk and demand spikes",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "id": "normal_usage",
                "title": "Usage pattern looks stable",
                "message": "No major saving rule fired in the latest 24-hour window.",
                "severity": "low",
                "savings_hint": "Continue monitoring appliance-level trends",
            }
        )

    return recommendations


async def get_recommendations(
    db: AsyncIOMotorDatabase,
    household_id: str,
    user_id: str,
) -> dict:
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

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    cursor = (
        db.readings.find(
            {"household_id": household_id, "timestamp": {"$gte": since}},
            {"_id": 0, "timestamp": 1, "energy_kwh": 1, "power_w": 1, "watts": 1},
        )
        .sort("timestamp", 1)
    )
    readings = pd.DataFrame(await cursor.to_list(length=None))
    summary = summarize_readings(readings)
    return {
        "household_id": household_id,
        "window_hours": 24,
        "summary": summary,
        "recommendations": evaluate_rules(summary),
    }
