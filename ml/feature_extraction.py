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
DATA_DIR = Path(__file__).parent / "data"

TAPO_COLUMN_MAP = {
    "timestamp_utc": "timestamp",
    "current_power": "power_w",
    "device_alias": "appliance_label",
    "appliance": "appliance_label",
    "state": "relay_state",
}

APPLIANCE_LABEL_MAP = {
    "kettle": "electric_kettle",
    "electric_kettle": "electric_kettle",
    "table_fan": "fan",
    "fan": "fan",
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


def extract_features_from_window(window: pd.Series) -> dict:
    """
    Extract a feature vector from a single power window (array of watts).

    Features:
        mean_power     - average watts during window
        max_power      - peak watts during window
        min_power      - minimum watts during window
        power_delta    - max - min swing
        std_power      - standard deviation (variance proxy)
        rise_time_s    - index of peak power (proxy for rise time)
        steady_state_w - median watts in stable middle third
        is_cyclic      - 1 if power crosses mean more than 4 times
        on_fraction    - fraction of window where power > ON_THRESHOLD_W
    """
    values = window.values.astype(float)
    n = len(values)
    if n == 0:
        return {}

    mean_p = float(np.mean(values))
    max_p = float(np.max(values))
    min_p = float(np.min(values))
    std_p = float(np.std(values))
    delta_p = max_p - min_p

    rise_idx = int(np.argmax(values))
    rise_time_s = float(rise_idx)

    third = max(1, n // 3)
    steady_state = float(np.median(values[third: 2 * third]))

    crossings = int(np.sum(np.diff(np.sign(values - mean_p)) != 0))
    is_cyclic = 1 if crossings > 4 else 0

    on_fraction = float(np.mean(values > ON_THRESHOLD_W))

    return {
        "mean_power": mean_p,
        "max_power": max_p,
        "min_power": min_p,
        "power_delta": delta_p,
        "std_power": std_p,
        "rise_time_s": rise_time_s,
        "steady_state_w": steady_state,
        "is_cyclic": is_cyclic,
        "on_fraction": on_fraction,
    }


def extract_all_features(df: pd.DataFrame, window_size: int = WINDOW_SIZE_S) -> pd.DataFrame:
    """
    Slide a window across each appliance group and extract features.
    Uses 50% overlap between consecutive windows.
    """
    records = []
    step = max(1, window_size // 2)

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
        group = group.reset_index(drop=True)
        power = group["power_w"]
        n = len(power)
        starts = [0] if n <= window_size else range(0, n - window_size + 1, step)

        for start in starts:
            window = power.iloc[start: start + window_size]
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
