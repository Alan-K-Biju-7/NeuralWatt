"""
Train a Prophet demand forecaster from NeuralWatt reading CSVs.

Example:
    python ml/forecast.py ml/data/appliance_data_real.csv
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd


DEFAULT_OUTPUT = Path("ml/data/forecast_24h.csv")


def add_cyclical_time_features(
    frame: pd.DataFrame,
    timestamp_col: str = "ds",
) -> pd.DataFrame:
    """
    Add sin/cos time encodings for forecasting feature experiments.

    This is intentionally not wired into the live Prophet endpoint yet. It gives
    tree-based forecasters a safe feature builder where 23:00 and 00:00 are
    treated as neighbouring hours.
    """
    if timestamp_col not in frame.columns:
        raise ValueError(f"Missing timestamp column: {timestamp_col}")

    result = frame.copy()
    timestamps = pd.to_datetime(result[timestamp_col], errors="coerce")
    hour = timestamps.dt.hour.fillna(0)
    weekday = timestamps.dt.dayofweek.fillna(0)
    result["sin_hour"] = np.sin(2 * np.pi * hour / 24)
    result["cos_hour"] = np.cos(2 * np.pi * hour / 24)
    result["sin_weekday"] = np.sin(2 * np.pi * weekday / 7)
    result["cos_weekday"] = np.cos(2 * np.pi * weekday / 7)
    return result


def extract_hw_features(series: pd.Series, seasonal_periods: int = 24) -> pd.DataFrame:
    """
    Return Holt-Winters level, trend, seasonal, and residual feature columns.

    The function is additive groundwork for a future tree-based forecaster. It
    gracefully returns zero-valued features when data is too short or the
    optional statsmodels dependency is unavailable.
    """
    clean = pd.to_numeric(series, errors="coerce").fillna(0.0)
    index = clean.index
    zero_features = pd.DataFrame(
        {
            "hw_level": np.zeros(len(clean)),
            "hw_trend": np.zeros(len(clean)),
            "hw_seasonal": np.zeros(len(clean)),
            "hw_residual": np.zeros(len(clean)),
        },
        index=index,
    )
    if len(clean) < 2 * seasonal_periods:
        return zero_features

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        model = ExponentialSmoothing(
            clean,
            trend="add",
            seasonal="add",
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        )
        fit = model.fit(optimized=True, remove_bias=True)
    except Exception:
        return zero_features

    return pd.DataFrame(
        {
            "hw_level": fit.level,
            "hw_trend": fit.trend,
            "hw_seasonal": fit.season,
            "hw_residual": clean.to_numpy() - fit.fittedvalues.to_numpy(),
        },
        index=index,
    )


def build_forecast_feature_frame(hourly: pd.DataFrame) -> pd.DataFrame:
    """
    Build experimental tree-model features from hourly forecast input.

    The live backend still uses Prophet. This helper is kept separate so the
    project can evaluate Random Forest/XGBoost forecasting later without
    changing the current endpoint contract.
    """
    if not {"ds", "y"}.issubset(hourly.columns):
        raise ValueError("hourly must contain ds and y columns")

    features = add_cyclical_time_features(hourly[["ds", "y"]])
    y = pd.to_numeric(features["y"], errors="coerce").fillna(0.0)
    features["lag_1h"] = y.shift(1).fillna(0.0)
    features["lag_24h"] = y.shift(24).fillna(0.0)
    features["rolling_6h_mean"] = (
        y.shift(1).rolling(6, min_periods=1).mean().fillna(0.0)
    )
    features["rolling_24h_mean"] = (
        y.shift(1).rolling(24, min_periods=1).mean().fillna(0.0)
    )
    hw_features = extract_hw_features(y, seasonal_periods=24).reset_index(drop=True)
    return pd.concat([features.reset_index(drop=True), hw_features], axis=1)


def _prepare_plot_cache() -> None:
    os.environ.setdefault(
        "XDG_CACHE_HOME",
        os.path.join(tempfile.gettempdir(), "neuralwatt-cache"),
    )
    os.environ.setdefault(
        "MPLCONFIGDIR",
        os.path.join(tempfile.gettempdir(), "neuralwatt-matplotlib"),
    )


def _find_timestamp_column(df: pd.DataFrame) -> str:
    for column in ("timestamp", "timestamp_utc", "created_at", "time"):
        if column in df.columns:
            return column
    raise ValueError("CSV must contain timestamp, timestamp_utc, created_at, or time")


def _energy_from_power(df: pd.DataFrame) -> pd.Series:
    if "power_w" not in df.columns:
        raise ValueError("CSV must contain energy_kwh or power_w")

    timestamps = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    power_w = pd.to_numeric(df["power_w"], errors="coerce").fillna(0.0).clip(lower=0)
    deltas = timestamps.diff().dt.total_seconds().div(3600)
    median_delta = deltas[(deltas > 0) & (deltas < 1)].median()
    if pd.isna(median_delta):
        median_delta = 5 / 3600
    deltas = deltas.fillna(median_delta).clip(lower=0, upper=1)
    return power_w * deltas / 1000


def load_readings(filepath: str | Path) -> pd.DataFrame:
    """
    Load readings and return hourly Prophet input columns: ds, y.
    """
    df = pd.read_csv(filepath)
    timestamp_col = _find_timestamp_column(df)
    df = df.rename(columns={timestamp_col: "timestamp"}).copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    if df.empty:
        raise ValueError("CSV has no valid timestamp rows")

    if "energy_kwh" in df.columns:
        energy = pd.to_numeric(df["energy_kwh"], errors="coerce").fillna(0.0)
        if energy.sum() <= 0 and "power_w" in df.columns:
            energy = _energy_from_power(df)
    else:
        energy = _energy_from_power(df)

    hourly = (
        pd.DataFrame({"timestamp": df["timestamp"], "energy_kwh": energy.clip(lower=0)})
        .set_index("timestamp")
        .resample("h")
        .sum()
        .reset_index()
    )
    hourly = hourly.rename(columns={"timestamp": "ds", "energy_kwh": "y"})
    hourly["ds"] = hourly["ds"].dt.tz_localize(None)
    hourly["y"] = hourly["y"].clip(lower=0)
    return hourly


def train_forecast_model(hourly: pd.DataFrame):
    if len(hourly) < 24:
        raise ValueError("At least 24 hourly points are required for forecasting")

    try:
        _prepare_plot_cache()
        from prophet import Prophet
    except ImportError as exc:
        raise RuntimeError(
            "Prophet is not installed. Run: pip install -r ml/requirements.txt"
        ) from exc

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=len(hourly) >= 24 * 7,
        yearly_seasonality=False,
        interval_width=0.8,
    )
    model.fit(hourly)
    return model


def predict_next_24h(model) -> pd.DataFrame:
    future = model.make_future_dataframe(periods=24, freq="h", include_history=False)
    forecast = model.predict(future)
    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    for column in ("yhat", "yhat_lower", "yhat_upper"):
        result[column] = result[column].clip(lower=0)
    return result


def save_forecast(forecast: pd.DataFrame, output: str | Path = DEFAULT_OUTPUT) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(output, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a 24-hour energy forecast")
    parser.add_argument("csv", help="Input readings CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path")
    args = parser.parse_args()

    hourly = load_readings(args.csv)
    model = train_forecast_model(hourly)
    forecast = predict_next_24h(model)
    output = save_forecast(forecast, args.output)
    print(f"Forecast saved to {output}")


if __name__ == "__main__":
    main()
