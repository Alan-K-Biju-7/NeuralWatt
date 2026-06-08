"""
Feature extraction for NILM appliance classification.

Input:  labelled CSV - columns: timestamp, power_w, appliance_label
Output: feature vectors per appliance event window

Tapo P110 exports are normalized by load_tapo_csv/load_csv:
    timestamp_utc/current_power/appliance -> timestamp/power_w/appliance_label
"""

from pathlib import Path

import pandas as pd
import numpy as np

SUPPORTED_APPLIANCES = [
    "fridge",
    "washing_machine",
    "geyser",
    "iron",
    "microwave",
    "mixer_grinder",
    "tv",
    "fan",
    "electric_kettle",
    "laptop_charger",
]

ON_THRESHOLD_W = 5.0
WINDOW_SIZE_S = 30
MIN_WINDOW_SAMPLES = 3
DATA_DIR = Path(__file__).parent / "data"

TAPO_COLUMN_MAP = {
    "timestamp_utc": "timestamp",
    "current_power": "power_w",
    "device_alias": "appliance_label",
    "appliance": "appliance_label",
    "state": "relay_state",
}

APPLIANCE_LABEL_MAP = {
    "fridge": "fridge",
    "iron": "iron",
    "kettle": "electric_kettle",
    "electric_kettle": "electric_kettle",
    "table_fan": "fan",
    "fan": "fan",
    "washing_machine": "washing_machine",
    "mixie": "mixer_grinder",
    "mixer": "mixer_grinder",
    "mixer_grinder": "mixer_grinder",
}

TAPO_HINT_COLUMNS = {
    "timestamp_utc",
    "timestamp_local",
    "plug_id",
    "plug_alias",
    "plug_model",
    "sample_interval_sec",
}

FEATURE_COLUMNS = [
    "mean_power",
    "max_power",
    "min_power",
    "median_power",
    "p10_power",
    "p25_power",
    "p75_power",
    "p90_power",
    "power_delta",
    "std_power",
    "steady_state_w",
    "active_mean_power",
    "active_max_power",
    "on_fraction",
    "zero_fraction",
    "high_power_fraction",
    "very_high_power_fraction",
    "transition_count",
    "mean_abs_step",
    "max_step_up",
    "max_step_down",
    "rise_time_s",
    "energy_kwh_est",
    "mean_voltage",
    "std_voltage",
    "mean_current",
    "max_current",
    "is_cyclic",
]


def _rename_known_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename Tapo/API variants to the NILM training schema."""
    rename = {}
    for source, target in TAPO_COLUMN_MAP.items():
        if source in df.columns and target not in df.columns:
            rename[source] = target
    return df.rename(columns=rename)


def _normalize_appliance_label(value: str) -> str:
    label = str(value).strip()
    return APPLIANCE_LABEL_MAP.get(label, label)


def _finalize_appliance_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean the canonical appliance readings frame."""
    df = _rename_known_columns(df)

    required = {"timestamp", "power_w", "appliance_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()
    df["power_w"] = (
        pd.to_numeric(df["power_w"], errors="coerce")
        .fillna(0.0)
        .clip(lower=0.0)
    )
    df["appliance_label"] = df["appliance_label"].map(_normalize_appliance_label)
    return df.sort_values("timestamp").reset_index(drop=True)


def _numeric_window_values(window: pd.DataFrame, column: str) -> np.ndarray:
    if column not in window.columns:
        return np.zeros(len(window), dtype=float)
    return (
        pd.to_numeric(window[column], errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
    )


def _window_time_features(window: pd.DataFrame) -> tuple[float, float, np.ndarray]:
    if "timestamp" not in window.columns or len(window) <= 1:
        sample_interval = 1.0
        duration = float(max(len(window) - 1, 0))
        return duration, sample_interval, np.full(len(window), sample_interval)

    timestamps = pd.to_datetime(window["timestamp"], errors="coerce")
    deltas = timestamps.diff().dt.total_seconds().dropna()
    deltas = deltas[deltas > 0]
    if deltas.empty:
        sample_interval = 1.0
        duration = float(max(len(window) - 1, 0))
        intervals = np.full(len(window), sample_interval)
    else:
        sample_interval = float(deltas.median())
        duration = float((timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds())
        intervals = np.concatenate(([sample_interval], deltas.to_numpy(dtype=float)))
    return max(duration, 0.0), sample_interval, intervals


def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a labelled appliance CSV and normalize known Tapo P110 column variants.

    Expected columns:
        timestamp       - ISO8601 datetime
        power_w         - active power in watts (float)
        appliance_label - string label e.g. 'fridge'
        capture_id      - optional capture/session identifier
    """
    df = pd.read_csv(filepath)
    if TAPO_HINT_COLUMNS.intersection(df.columns) and "capture_id" not in df.columns:
        df["capture_id"] = Path(filepath).stem
    return _finalize_appliance_frame(df)


def load_tapo_csv(filepath: str, label: str | None = None) -> pd.DataFrame:
    """
    Load a Tapo P110 export CSV and normalize to the canonical NILM schema.
    """
    df = pd.read_csv(filepath)
    df = _rename_known_columns(df)
    if label is not None:
        df["appliance_label"] = label
    if "capture_id" not in df.columns:
        df["capture_id"] = Path(filepath).stem
    return _finalize_appliance_frame(df)


def extract_features_from_window(window: pd.DataFrame | pd.Series) -> dict:
    """
    Extract a feature vector from a single appliance power window.

    The feature set intentionally mixes steady-state, transient, duty-cycle,
    and light electrical-context signals. This helps separate appliances that
    sit in similar wattage bands, such as fridge and fan.
    """
    if isinstance(window, pd.Series):
        window = pd.DataFrame({"power_w": window})

    values = _numeric_window_values(window, "power_w")
    n = len(values)
    if n == 0:
        return {}

    duration_s, sample_interval_s, intervals = _window_time_features(window)
    mean_p = float(np.mean(values))
    max_p = float(np.max(values))
    min_p = float(np.min(values))
    median_p = float(np.median(values))
    std_p = float(np.std(values))
    delta_p = max_p - min_p
    p10, p25, p75, p90 = np.percentile(values, [10, 25, 75, 90])

    rise_idx = int(np.argmax(values))
    rise_time_s = float(rise_idx * sample_interval_s)

    third = max(1, n // 3)
    steady_state = float(np.median(values[third: 2 * third]))

    centered = values - mean_p
    crossings = int(np.sum(np.diff(np.sign(centered)) != 0))
    is_cyclic = 1 if crossings > 4 else 0

    active_mask = values > ON_THRESHOLD_W
    on_fraction = float(np.mean(active_mask))
    zero_fraction = float(np.mean(values <= ON_THRESHOLD_W))
    high_power_fraction = float(np.mean(values >= 100.0))
    very_high_power_fraction = float(np.mean(values >= 1000.0))
    active_values = values[active_mask]
    active_mean = float(np.mean(active_values)) if len(active_values) else 0.0
    active_max = float(np.max(active_values)) if len(active_values) else 0.0

    on_state = active_mask.astype(int)
    transition_count = int(np.sum(np.abs(np.diff(on_state)))) if n > 1 else 0

    steps = np.diff(values)
    mean_abs_step = float(np.mean(np.abs(steps))) if len(steps) else 0.0
    max_step_up = float(np.max(steps)) if len(steps) else 0.0
    max_step_down = float(abs(np.min(steps))) if len(steps) else 0.0

    if len(intervals) != n:
        intervals = np.full(n, sample_interval_s)
    energy_kwh = float(np.sum(values * intervals) / 3_600_000.0)

    voltage = _numeric_window_values(window, "voltage_v")
    current = _numeric_window_values(window, "current_a")

    return {
        "mean_power": mean_p,
        "max_power": max_p,
        "min_power": min_p,
        "median_power": median_p,
        "p10_power": float(p10),
        "p25_power": float(p25),
        "p75_power": float(p75),
        "p90_power": float(p90),
        "power_delta": delta_p,
        "std_power": std_p,
        "steady_state_w": steady_state,
        "active_mean_power": active_mean,
        "active_max_power": active_max,
        "on_fraction": on_fraction,
        "zero_fraction": zero_fraction,
        "high_power_fraction": high_power_fraction,
        "very_high_power_fraction": very_high_power_fraction,
        "transition_count": transition_count,
        "mean_abs_step": mean_abs_step,
        "max_step_up": max_step_up,
        "max_step_down": max_step_down,
        "rise_time_s": rise_time_s,
        "duration_s": duration_s,
        "sample_interval_median_s": sample_interval_s,
        "energy_kwh_est": energy_kwh,
        "mean_voltage": float(np.mean(voltage)) if len(voltage) else 0.0,
        "std_voltage": float(np.std(voltage)) if len(voltage) else 0.0,
        "mean_current": float(np.mean(current)) if len(current) else 0.0,
        "max_current": float(np.max(current)) if len(current) else 0.0,
        "is_cyclic": is_cyclic,
    }


def extract_all_features(df: pd.DataFrame, window_size: int = WINDOW_SIZE_S) -> pd.DataFrame:
    """
    Slide a time window across each appliance capture and extract features.
    Uses 50% overlap between consecutive windows.
    """
    records = []
    step_s = max(1, window_size // 2)

    session_col = next(
        (col for col in ("capture_id", "session_id") if col in df.columns),
        None,
    )
    grouped = (
        df.groupby(["appliance_label", session_col], sort=False, dropna=False)
        if session_col
        else df.groupby("appliance_label", sort=False)
    )

    for key, group in grouped:
        label = key[0] if isinstance(key, tuple) else key
        group = group.sort_values("timestamp").reset_index(drop=True)
        n = len(group)
        if n == 0:
            continue

        if "timestamp" in group.columns and n >= MIN_WINDOW_SAMPLES:
            start_time = group["timestamp"].iloc[0]
            end_time = group["timestamp"].iloc[-1]
            window_delta = pd.Timedelta(seconds=window_size)
            step_delta = pd.Timedelta(seconds=step_s)
            starts = []
            current = start_time
            while current <= end_time:
                starts.append(current)
                current += step_delta

            for start in starts:
                stop = start + window_delta
                window = group[
                    (group["timestamp"] >= start)
                    & (group["timestamp"] < stop)
                ]
                if len(window) < MIN_WINDOW_SAMPLES:
                    continue
                features = extract_features_from_window(window)
                if not features:
                    continue
                features["appliance_label"] = label
                records.append(features)
            continue

        step_rows = max(1, window_size // 2)
        starts = [0] if n <= window_size else range(0, n - window_size + 1, step_rows)
        for start in starts:
            window = group.iloc[start: start + window_size]
            features = extract_features_from_window(window)
            if not features:
                continue
            features["appliance_label"] = label
            records.append(features)

    if not records:
        raise ValueError("No feature windows extracted. Check CSV data and window size.")

    return pd.DataFrame(records)


def load_and_extract(filepath: str, window_size: int = WINDOW_SIZE_S) -> pd.DataFrame:
    """Convenience: load CSV and return feature DataFrame."""
    df = load_csv(filepath)
    return extract_all_features(df, window_size=window_size)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract NILM features from labelled CSV")
    parser.add_argument("csv", help="Path to raw or canonical labelled appliance CSV")
    parser.add_argument("--window", type=int, default=WINDOW_SIZE_S, help="Window size in rows")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "features_extracted.csv"),
        help="Output feature CSV path",
    )
    args = parser.parse_args()

    features = load_and_extract(args.csv, window_size=args.window)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    print(features.head())
    print(f"\nExtracted {len(features)} feature windows")
    print(f"Labels found: {features['appliance_label'].unique().tolist()}")
    print(f"Features saved -> {output_path}")
