from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import tempfile

import pandas as pd
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.household_service import get_household_by_id


def _prepare_plot_cache() -> None:
    os.environ.setdefault(
        "XDG_CACHE_HOME",
        os.path.join(tempfile.gettempdir(), "neuralwatt-cache"),
    )
    os.environ.setdefault(
        "MPLCONFIGDIR",
        os.path.join(tempfile.gettempdir(), "neuralwatt-matplotlib"),
    )


def _energy_from_power(frame: pd.DataFrame) -> pd.Series:
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


def hourly_energy_frame(readings: pd.DataFrame) -> pd.DataFrame:
    if readings.empty:
        return pd.DataFrame(columns=["ds", "y"])

    frame = readings.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")
    if frame.empty:
        return pd.DataFrame(columns=["ds", "y"])

    if "energy_kwh" in frame.columns:
        energy = pd.to_numeric(frame["energy_kwh"], errors="coerce").fillna(0.0)
        if energy.sum() <= 0:
            energy = _energy_from_power(frame)
    else:
        energy = _energy_from_power(frame)

    hourly = (
        pd.DataFrame({"timestamp": frame["timestamp"], "energy_kwh": energy.clip(lower=0)})
        .set_index("timestamp")
        .resample("h")
        .sum()
        .reset_index()
    )
    hourly = hourly.rename(columns={"timestamp": "ds", "energy_kwh": "y"})
    hourly["ds"] = hourly["ds"].dt.tz_localize(None)
    hourly["y"] = hourly["y"].clip(lower=0)
    return hourly


async def get_readings_for_forecast(
    db: AsyncIOMotorDatabase,
    household_id: str,
    user_id: str,
    days: int = 30,
) -> pd.DataFrame:
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

    since = datetime.now(timezone.utc) - timedelta(days=days)
    cursor = (
        db.readings.find(
            {"household_id": household_id, "timestamp": {"$gte": since}},
            {"_id": 0, "timestamp": 1, "energy_kwh": 1, "power_w": 1, "watts": 1},
        )
        .sort("timestamp", 1)
    )
    docs = await cursor.to_list(length=None)
    frame = pd.DataFrame(docs)
    if "power_w" not in frame.columns and "watts" in frame.columns:
        frame["power_w"] = frame["watts"]
    return frame


def run_forecast(readings: pd.DataFrame) -> list[dict]:
    hourly = hourly_energy_frame(readings)
    if len(hourly) < 24:
        raise ValueError("At least 24 hourly points are required for forecasting")

    try:
        _prepare_plot_cache()
        from prophet import Prophet
    except ImportError as exc:
        raise RuntimeError(
            "Prophet is not installed in the backend environment"
        ) from exc

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=len(hourly) >= 24 * 7,
        yearly_seasonality=False,
        interval_width=0.8,
    )
    model.fit(hourly)
    future = model.make_future_dataframe(periods=24, freq="h", include_history=False)
    forecast = model.predict(future)

    points = []
    for row in forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_dict("records"):
        points.append(
            {
                "hour": row["ds"].isoformat(),
                "predicted_kwh": round(max(float(row["yhat"]), 0.0), 4),
                "lower_kwh": round(max(float(row["yhat_lower"]), 0.0), 4),
                "upper_kwh": round(max(float(row["yhat_upper"]), 0.0), 4),
            }
        )
    return points
