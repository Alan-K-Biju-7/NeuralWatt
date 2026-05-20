"""
Feature extraction for NILM appliance classification.

Input:  labelled CSV — columns: timestamp, power_w, appliance_label
Output: feature vectors per appliance event window

TODO (Tapo P110): When real plug data arrives, map Tapo API fields:
    current_power -> power_w
    timestamp     -> timestamp
    device_alias  -> appliance_label
"""

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
    "laptop_charger",
]

ON_THRESHOLD_W = 5.0
WINDOW_SIZE_S = 30


def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a labelled appliance CSV.

    Expected columns:
        timestamp       - ISO8601 datetime
        power_w         - active power in watts (float)
        appliance_label - string label e.g. 'fridge'

    TODO: Add Tapo P110 column rename here once real data format is confirmed.
    """
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    required = {"timestamp", "power_w", "appliance_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    df["power_w"] = pd.to_numeric(df["power_w"], errors="coerce").fillna(0.0)
    return df


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

    for label, group in df.groupby("appliance_label"):
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
    import sys
    if len(sys.argv) < 2:
        print("Usage: python feature_extraction.py <path_to_csv>")
        sys.exit(1)
    features = load_and_extract(sys.argv[1])
    print(features.head())
    print(f"\nExtracted {len(features)} feature windows")
    print(f"Labels found: {features['appliance_label'].unique().tolist()}")
