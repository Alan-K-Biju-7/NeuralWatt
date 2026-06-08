"""
Shared NILM prediction helpers.

This module keeps inference on the same feature contract used by training and
evaluation. It accepts raw Tapo/canonical readings, extracts window features,
and returns appliance predictions from a saved model artifact.
"""

from __future__ import annotations

from pathlib import Path
import pickle

import pandas as pd

try:
    from .feature_extraction import (
        FEATURE_COLUMNS,
        WINDOW_SIZE_S,
        _finalize_appliance_frame,
        _rename_known_columns,
        extract_all_features,
    )
except ImportError:
    from feature_extraction import (  # type: ignore
        FEATURE_COLUMNS,
        WINDOW_SIZE_S,
        _finalize_appliance_frame,
        _rename_known_columns,
        extract_all_features,
    )


DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "nilm_v1.pkl"
UNKNOWN_LABEL = "unknown"


def load_model_artifact(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict:
    """Load a serialized NILM model artifact and validate its public contract."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"NILM model not found at {path}. Train it with: "
            "python ml/train_nilm.py --data ml/data/appliance_data_real.csv"
        )

    with path.open("rb") as f:
        artifact = pickle.load(f)

    required = {"model", "label_encoder", "feature_cols"}
    missing = required - set(artifact.keys())
    if missing:
        raise ValueError(f"Model artifact missing keys: {sorted(missing)}")
    return artifact


def normalize_prediction_readings(
    readings: pd.DataFrame,
    *,
    label: str = UNKNOWN_LABEL,
    capture_id: str = "prediction",
) -> pd.DataFrame:
    """Normalize prediction input into the canonical appliance-reading schema."""
    df = _rename_known_columns(readings.copy())
    rename = {}
    if "watts" in df.columns and "power_w" not in df.columns:
        rename["watts"] = "power_w"
    if "voltage" in df.columns and "voltage_v" not in df.columns:
        rename["voltage"] = "voltage_v"
    if "current" in df.columns and "current_a" not in df.columns:
        rename["current"] = "current_a"
    if rename:
        df = df.rename(columns=rename)

    if "appliance_label" not in df.columns:
        df["appliance_label"] = label
    elif label != UNKNOWN_LABEL:
        df["appliance_label"] = label

    if "capture_id" not in df.columns:
        df["capture_id"] = capture_id

    return _finalize_appliance_frame(df)


def load_prediction_csv(
    csv_path: str | Path,
    *,
    label: str = UNKNOWN_LABEL,
) -> pd.DataFrame:
    """Load an unlabeled or labeled CSV for prediction."""
    path = Path(csv_path)
    df = pd.read_csv(path)
    return normalize_prediction_readings(df, label=label, capture_id=path.stem)


def extract_prediction_features(
    readings: pd.DataFrame,
    *,
    window_size_s: int = WINDOW_SIZE_S,
) -> pd.DataFrame:
    """Extract model-ready window features from normalized prediction readings."""
    return extract_all_features(readings, window_size=window_size_s)


def _feature_columns_for(artifact: dict) -> list[str]:
    feature_cols = list(artifact.get("feature_cols") or FEATURE_COLUMNS)
    if not feature_cols:
        raise ValueError("Model artifact does not define feature columns.")
    return feature_cols


def predict_feature_frame(artifact: dict, features: pd.DataFrame) -> list[dict]:
    """Predict appliances for an extracted feature frame."""
    model = artifact["model"]
    label_encoder = artifact["label_encoder"]
    feature_cols = _feature_columns_for(artifact)

    missing = set(feature_cols) - set(features.columns)
    if missing:
        raise ValueError(f"Prediction features missing columns: {sorted(missing)}")

    classes = label_encoder.classes_.tolist()
    X = features[feature_cols].to_numpy()
    encoded_predictions = model.predict(X)
    predicted_labels = label_encoder.inverse_transform(encoded_predictions)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)
    else:
        probabilities = None

    predictions = []
    for index, predicted in enumerate(predicted_labels):
        if probabilities is None:
            probability_map = {
                cls: 1.0 if cls == predicted else 0.0
                for cls in classes
            }
        else:
            probability_map = {
                cls: float(probabilities[index][class_index])
                for class_index, cls in enumerate(classes)
            }

        confidence = float(probability_map.get(predicted, 0.0))
        predictions.append(
            {
                "window_index": index,
                "predicted_appliance": str(predicted),
                "confidence": confidence,
                "probabilities": probability_map,
            }
        )

    return predictions


def predict_readings(
    artifact: dict,
    readings: pd.DataFrame,
    *,
    window_size_s: int = WINDOW_SIZE_S,
    label: str = UNKNOWN_LABEL,
    capture_id: str = "prediction",
) -> dict:
    """Run the full prediction pipeline for raw readings."""
    normalized = normalize_prediction_readings(
        readings,
        label=label,
        capture_id=capture_id,
    )
    features = extract_prediction_features(normalized, window_size_s=window_size_s)
    metadata = artifact.get("metadata") or {}
    classes = artifact["label_encoder"].classes_.tolist()

    return {
        "classes": classes,
        "feature_set_version": metadata.get("feature_set_version"),
        "window_size_s": window_size_s,
        "window_count": int(len(features)),
        "predictions": predict_feature_frame(artifact, features),
    }


def predictions_to_frame(predictions: list[dict]) -> pd.DataFrame:
    """Flatten prediction dictionaries into a CSV-friendly table."""
    rows = []
    for item in predictions:
        row = {
            "window_index": item["window_index"],
            "predicted_appliance": item["predicted_appliance"],
            "confidence": item["confidence"],
        }
        row.update({
            f"prob_{label}": probability
            for label, probability in item["probabilities"].items()
        })
        rows.append(row)
    return pd.DataFrame(rows)
