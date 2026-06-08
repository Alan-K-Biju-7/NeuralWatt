"""
Predict appliance signatures from a raw CSV using a trained NILM artifact.

Example:
    python ml/predict_nilm.py --csv ml/data/appliance_data_real.csv --limit 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prediction import (
    DEFAULT_MODEL_PATH,
    UNKNOWN_LABEL,
    load_model_artifact,
    load_prediction_csv,
    predict_readings,
    predictions_to_frame,
)


def _print_table(predictions: list[dict], limit: int | None = None) -> None:
    rows = predictions[:limit] if limit is not None else predictions
    if not rows:
        print("No prediction windows were produced.")
        return

    print(f"{'Window':>6}  {'Prediction':<20} {'Confidence':>10}")
    print("-" * 41)
    for item in rows:
        print(
            f"{item['window_index']:>6}  "
            f"{item['predicted_appliance']:<20} "
            f"{item['confidence'] * 100:>9.2f}%"
        )

    hidden = len(predictions) - len(rows)
    if hidden > 0:
        print(f"... {hidden} more windows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict NILM appliance windows")
    parser.add_argument("--csv", required=True, help="Raw or canonical readings CSV")
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL_PATH),
        help="Path to trained nilm_v1.pkl artifact",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Prediction window size in seconds",
    )
    parser.add_argument(
        "--label",
        default=UNKNOWN_LABEL,
        help="Optional source label used only for window grouping",
    )
    parser.add_argument("--output", help="Optional CSV path for prediction rows")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a table")
    parser.add_argument("--limit", type=int, help="Limit table rows printed to stdout")
    args = parser.parse_args()

    artifact = load_model_artifact(args.model)
    readings = load_prediction_csv(args.csv, label=args.label)
    result = predict_readings(
        artifact,
        readings,
        window_size_s=args.window,
        label=args.label,
        capture_id=Path(args.csv).stem,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        predictions_to_frame(result["predictions"]).to_csv(output_path, index=False)
        print(f"Predictions saved -> {output_path}")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"NILM predictions: {result['window_count']} windows | "
            f"classes: {', '.join(result['classes'])}"
        )
        _print_table(result["predictions"], limit=args.limit)


if __name__ == "__main__":
    main()
