"""
Merge individual Tapo P110 appliance exports into one labelled CSV.

Run after adding new appliance data to data/raw/.
"""

from pathlib import Path
import sys

import pandas as pd

ML_DIR = Path(__file__).resolve().parents[1]
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from feature_extraction import load_tapo_csv  # noqa: E402

RAW_DIR = Path(__file__).parent / "raw"
OUT_FILE = Path(__file__).parent / "appliance_data_real.csv"
QUALITY_FILE = Path(__file__).parent / "raw_quality_report.csv"

# Map filename -> canonical appliance label.
FILES = {
    "alaina_plug4_kettle_boil_2026-06-02_S001.csv": "electric_kettle",
    "alaina_plug4_kettle_boil_2026-06-02_S002.csv": "electric_kettle",
    "alaina_plug4_kettle_boil_2026-06-02_S003.csv": "electric_kettle",
    "alaina_plug4_tablefan_speed1_2026-06-03_S004.csv": "fan",
    "alaina_plug4_tablefan_speed2_2026-06-03_S005.csv": "fan",
    "alaina_plug4_tablefan_speed3_2026-06-03_S006.csv": "fan",
    "anllia_plug1_mixer_final_2026-06-02_S003.csv": "mixer_grinder",
}

EXPECTED_MAX_W = {
    "electric_kettle": 2500.0,
    "fan": 150.0,
    "mixer_grinder": 1000.0,
}

OUTPUT_COLUMNS = [
    "timestamp",
    "power_w",
    "appliance_label",
    "capture_id",
    "session_id",
    "mode",
    "sample_interval_sec",
    "team_member",
    "plug_id",
    "plug_alias",
    "plug_model",
    "voltage_v",
    "current_a",
    "energy_today_kwh",
    "energy_this_month_kwh",
    "energy_total_kwh",
    "relay_state",
    "rssi",
    "signal_level",
    "notes",
]


def summarize_quality(filename: str, df: pd.DataFrame) -> dict:
    """Return lightweight source-quality checks for one capture."""
    gaps = df["timestamp"].sort_values().diff().dt.total_seconds().dropna()
    sample_interval = pd.to_numeric(
        df.get("sample_interval_sec", pd.Series(dtype=float)),
        errors="coerce",
    ).median()
    if pd.isna(sample_interval) or sample_interval <= 0:
        sample_interval = float(gaps.median()) if len(gaps) else 0.0

    max_gap_s = float(gaps.max()) if len(gaps) else 0.0
    missing_gap_count = int((gaps > sample_interval * 1.5).sum()) if sample_interval else 0
    estimated_missing_rows = (
        int(((gaps / sample_interval).round() - 1).clip(lower=0).sum())
        if sample_interval
        else 0
    )
    label = df["appliance_label"].iloc[0]
    max_expected_w = EXPECTED_MAX_W.get(label, float("inf"))

    return {
        "file": filename,
        "rows": int(len(df)),
        "appliance_label": label,
        "session_id": df["session_id"].iloc[0] if "session_id" in df.columns else "",
        "mode": df["mode"].iloc[0] if "mode" in df.columns else "",
        "sample_interval_sec": float(sample_interval) if sample_interval else 0.0,
        "min_power_w": float(df["power_w"].min()),
        "mean_power_w": float(df["power_w"].mean()),
        "max_power_w": float(df["power_w"].max()),
        "nonzero_rows": int((df["power_w"] > 5.0).sum()),
        "max_gap_s": max_gap_s,
        "missing_gap_count": missing_gap_count,
        "estimated_missing_rows": estimated_missing_rows,
        "outlier_rows": int((df["power_w"] > max_expected_w).sum()),
    }


def main() -> None:
    dfs = []
    quality_rows = []

    for filename, label in FILES.items():
        path = RAW_DIR / filename
        if not path.exists():
            print(f"MISSING: {path}")
            continue

        df = load_tapo_csv(str(path), label=label)
        dfs.append(df)
        quality_rows.append(summarize_quality(filename, df))
        print(f"Loaded {len(df)} rows for '{label}' from {filename}")

    if not dfs:
        raise SystemExit("No raw CSV files were loaded.")

    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.sort_values("timestamp").reset_index(drop=True)
    ordered_cols = [col for col in OUTPUT_COLUMNS if col in merged.columns]
    extra_cols = [col for col in merged.columns if col not in ordered_cols]
    merged = merged[ordered_cols + extra_cols]
    merged.to_csv(OUT_FILE, index=False)

    quality = pd.DataFrame(quality_rows)
    quality.to_csv(QUALITY_FILE, index=False)

    print(f"\nMerged {len(merged)} total rows -> {OUT_FILE}")
    print(f"Quality report -> {QUALITY_FILE}")
    print(f"Class distribution:\n{merged['appliance_label'].value_counts()}")


if __name__ == "__main__":
    main()
