"""
Validate NeuralWatt time-series stationarity before forecasting.

The Augmented Dickey-Fuller test checks whether a series has a unit root. A
small p-value indicates stationarity and supports using the series without
first-order differencing.

Example:
    python ml/validate_data.py \
      --data ml/data/appliance_data_real.csv \
      --timestamp-column timestamp \
      --power-column power_w \
      --resample h \
      --output ml/results/stationarity_report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_OUTPUT = Path("ml/results/stationarity_report.json")


def _find_timestamp_column(frame: pd.DataFrame) -> str | None:
    for column in ("timestamp", "timestamp_utc", "created_at", "time", "ds"):
        if column in frame.columns:
            return column
    return None


def _energy_from_power(frame: pd.DataFrame, timestamp_col: str, power_col: str) -> pd.Series:
    timestamps = pd.to_datetime(frame[timestamp_col], utc=True, errors="coerce")
    power_w = pd.to_numeric(frame[power_col], errors="coerce").fillna(0.0).clip(lower=0)
    deltas = timestamps.diff().dt.total_seconds().div(3600)
    median_delta = deltas[(deltas > 0) & (deltas < 1)].median()
    if pd.isna(median_delta):
        median_delta = 5 / 3600
    deltas = deltas.fillna(median_delta).clip(lower=0, upper=1)
    return power_w * deltas / 1000


def build_validation_series(
    frame: pd.DataFrame,
    *,
    column: str | None = None,
    timestamp_column: str | None = None,
    energy_column: str | None = None,
    power_column: str | None = None,
    resample: str | None = None,
) -> tuple[pd.Series, dict]:
    """
    Build a numeric series suitable for ADF testing.

    Prefer `energy_column` for true forecast-target validation. If only power is
    available, the function estimates interval energy before optional resampling.
    """
    timestamp_column = timestamp_column or _find_timestamp_column(frame)
    metadata = {
        "timestamp_column": timestamp_column,
        "source_column": column or energy_column or power_column,
        "resample": resample,
    }

    working = frame.copy()
    if timestamp_column and timestamp_column in working.columns:
        working[timestamp_column] = pd.to_datetime(
            working[timestamp_column],
            utc=True,
            errors="coerce",
        )
        working = working.dropna(subset=[timestamp_column]).sort_values(timestamp_column)

    if energy_column:
        if energy_column not in working.columns:
            raise ValueError(f"Column not found: {energy_column}")
        values = pd.to_numeric(working[energy_column], errors="coerce").fillna(0.0)
        metadata["series_kind"] = "energy"
    elif power_column:
        if not timestamp_column:
            raise ValueError("timestamp_column is required when using power_column")
        if power_column not in working.columns:
            raise ValueError(f"Column not found: {power_column}")
        values = _energy_from_power(working, timestamp_column, power_column)
        metadata["series_kind"] = "estimated_energy_from_power"
    elif column:
        if column not in working.columns:
            raise ValueError(f"Column not found: {column}")
        values = pd.to_numeric(working[column], errors="coerce").fillna(0.0)
        metadata["series_kind"] = "raw_numeric"
    else:
        raise ValueError("Provide one of --energy-column, --power-column, or --column")

    if timestamp_column and timestamp_column in working.columns:
        values = pd.Series(values.to_numpy(), index=working[timestamp_column])
    else:
        values = pd.Series(values.to_numpy())

    values = values.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if resample:
        if not isinstance(values.index, pd.DatetimeIndex):
            raise ValueError("resample requires a timestamp column")
        values = values.resample(resample).sum().dropna()
        metadata["series_kind"] = f"{metadata['series_kind']}_{resample}_sum"

    return values.astype(float), metadata


def run_adf_test(series: pd.Series, series_name: str = "energy") -> dict:
    """
    Run the Augmented Dickey-Fuller test and return a JSON-safe report.
    """
    clean = pd.to_numeric(series, errors="coerce").dropna()
    clean = clean[clean.notna()]
    if len(clean) < 20:
        raise ValueError("Series too short for ADF test; need at least 20 observations")
    if clean.nunique() < 2:
        raise ValueError("ADF test requires a non-constant series")

    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError as exc:
        raise RuntimeError(
            "statsmodels is required for ADF validation. Install ml/requirements.txt."
        ) from exc

    statistic, p_value, lags_used, observations, critical_values, icbest = adfuller(
        clean,
        autolag="AIC",
    )
    is_stationary = bool(p_value < 0.05)
    return {
        "series_name": series_name,
        "n_observations": int(observations),
        "adf_statistic": round(float(statistic), 6),
        "p_value": round(float(p_value), 8),
        "num_lags_used": int(lags_used),
        "icbest": round(float(icbest), 6),
        "critical_values": {
            key: round(float(value), 6)
            for key, value in critical_values.items()
        },
        "is_stationary": is_stationary,
        "recommendation": (
            "Series is stationary at p < 0.05. Differencing is not required "
            "before tree-based forecasting."
            if is_stationary
            else "Series is non-stationary at p >= 0.05. Consider "
            "first-order differencing before forecasting."
        ),
    }


def validate_csv(
    data_path: str | Path,
    *,
    column: str | None = None,
    timestamp_column: str | None = None,
    energy_column: str | None = None,
    power_column: str | None = None,
    resample: str | None = None,
) -> dict:
    frame = pd.read_csv(data_path)
    series, metadata = build_validation_series(
        frame,
        column=column,
        timestamp_column=timestamp_column,
        energy_column=energy_column,
        power_column=power_column,
        resample=resample,
    )
    source_name = metadata["source_column"] or "energy"
    report = run_adf_test(series, series_name=str(source_name))
    report.update(
        {
            "data_path": str(data_path),
            "series_points": int(len(series)),
            **metadata,
        }
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an ADF stationarity test")
    parser.add_argument("--data", required=True, help="Input CSV path")
    parser.add_argument("--column", help="Raw numeric column to test")
    parser.add_argument("--timestamp-column", help="Timestamp column for sorting/resampling")
    parser.add_argument("--energy-column", help="Energy column to test")
    parser.add_argument("--power-column", help="Power column used to estimate interval energy")
    parser.add_argument("--resample", help="Optional pandas frequency, such as h or D")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="JSON report output path")
    args = parser.parse_args()

    report = validate_csv(
        args.data,
        column=args.column,
        timestamp_column=args.timestamp_column,
        energy_column=args.energy_column,
        power_column=args.power_column,
        resample=args.resample,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("NeuralWatt ADF stationarity validation")
    print(f"Data: {report['data_path']}")
    print(f"Series: {report['series_name']} ({report['series_kind']})")
    print(f"ADF statistic: {report['adf_statistic']}")
    print(f"p-value: {report['p_value']}")
    print(f"Stationary: {report['is_stationary']}")
    print(f"Recommendation: {report['recommendation']}")
    print(f"Report saved to: {output}")


if __name__ == "__main__":
    main()
