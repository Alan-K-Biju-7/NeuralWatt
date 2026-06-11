"""
Explain the trained NILM model with SHAP feature importance.

Example:
    python ml/explain.py --model ml/models/nilm_v1.pkl --features ml/data/features_extracted.csv
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd


DEFAULT_MODEL = Path("ml/models/nilm_v1.pkl")
DEFAULT_FEATURES = Path("ml/data/features_extracted.csv")
DEFAULT_OUTPUT = Path("ml/results/shap_importance.json")

IGNORED_COLUMNS = {
    "appliance_label",
    "label",
    "capture_id",
    "session_id",
    "window_start",
    "window_end",
    "start_time",
    "end_time",
}


def _prepare_plot_cache() -> None:
    os.environ.setdefault(
        "XDG_CACHE_HOME",
        os.path.join(tempfile.gettempdir(), "neuralwatt-cache"),
    )
    os.environ.setdefault(
        "MPLCONFIGDIR",
        os.path.join(tempfile.gettempdir(), "neuralwatt-matplotlib"),
    )


def _load_artifact(model_path: str | Path):
    with Path(model_path).open("rb") as handle:
        return pickle.load(handle)


def _model_from_artifact(artifact):
    if isinstance(artifact, dict):
        for key in ("model", "pipeline", "classifier"):
            if key in artifact:
                return artifact[key]
    return artifact


def _feature_columns(artifact, frame: pd.DataFrame) -> list[str]:
    if isinstance(artifact, dict):
        for key in ("feature_cols", "feature_columns"):
            cols = artifact.get(key)
            if cols:
                return [col for col in cols if col in frame.columns]
    return [
        col
        for col in frame.columns
        if col not in IGNORED_COLUMNS and pd.api.types.is_numeric_dtype(frame[col])
    ]


def _mean_abs_shap(shap_values) -> np.ndarray:
    if isinstance(shap_values, list):
        return np.mean([np.abs(values).mean(axis=0) for values in shap_values], axis=0)

    values = np.asarray(shap_values)
    if values.ndim == 3:
        return np.abs(values).mean(axis=(0, 2))
    return np.abs(values).mean(axis=0)


def explain_model(
    model_path: str | Path = DEFAULT_MODEL,
    features_path: str | Path = DEFAULT_FEATURES,
    output_path: str | Path = DEFAULT_OUTPUT,
    sample_size: int = 500,
) -> dict:
    try:
        _prepare_plot_cache()
        import shap
    except ImportError as exc:
        raise RuntimeError(
            "SHAP is not installed. Run: pip install -r ml/requirements.txt"
        ) from exc

    artifact = _load_artifact(model_path)
    model = _model_from_artifact(artifact)
    frame = pd.read_csv(features_path)
    feature_cols = _feature_columns(artifact, frame)
    if not feature_cols:
        raise ValueError("No numeric feature columns found for SHAP explanation")

    sample = frame[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    sample = sample.head(sample_size)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)
    mean_abs = _mean_abs_shap(shap_values)
    ranked = sorted(
        [
            {"feature": feature, "mean_abs_shap": float(score)}
            for feature, score in zip(feature_cols, mean_abs)
        ],
        key=lambda row: row["mean_abs_shap"],
        reverse=True,
    )

    result = {
        "model": str(model_path),
        "features": str(features_path),
        "sample_size": int(len(sample)),
        "feature_importance": ranked,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Explain NILM feature importance with SHAP")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--features", default=str(DEFAULT_FEATURES))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--sample-size", type=int, default=500)
    args = parser.parse_args()

    result = explain_model(args.model, args.features, args.output, args.sample_size)
    print(f"Wrote SHAP importance for {result['sample_size']} windows to {args.output}")


if __name__ == "__main__":
    main()
