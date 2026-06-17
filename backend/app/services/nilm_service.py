import json
from pathlib import Path
import sys

from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.nilm import NILMPredictRequest, NILMPredictResponse, NILMWindowPrediction


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_model_path() -> Path:
    path = Path(settings.nilm_model_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _resolve_metadata_path() -> Path:
    return REPO_ROOT / "ml" / "models" / "nilm_v1_metadata.json"


def _resolve_shap_path() -> Path:
    return REPO_ROOT / "ml" / "results" / "shap_importance.json"


def _ensure_repo_on_path() -> None:
    repo_path = str(REPO_ROOT)
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)


def _request_to_records(payload: NILMPredictRequest) -> list[dict]:
    records = []
    for reading in payload.readings:
        records.append(
            {
                "timestamp": reading.timestamp,
                "power_w": reading.power_w,
                "voltage_v": reading.voltage_v,
                "current_a": reading.current_a,
            }
        )
    return records


def predict_nilm_windows(payload: NILMPredictRequest) -> NILMPredictResponse:
    """
    Classify submitted reading windows with the trained NILM model.

    ML dependencies are imported lazily so the backend remains usable before the
    model artifact has been trained or ML packages are installed in production.
    """
    _ensure_repo_on_path()

    try:
        import pandas as pd
        from ml.prediction import load_model_artifact, predict_readings
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "NILM prediction dependencies are not installed. Install "
                "ml/requirements.txt or use a backend image with ML packages."
            ),
        ) from exc

    model_path = _resolve_model_path()
    try:
        artifact = load_model_artifact(model_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NILM model dependency is missing: {exc.name}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NILM model could not be loaded: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NILM model could not be loaded: {exc}",
        ) from exc

    frame = pd.DataFrame(_request_to_records(payload))
    try:
        result = predict_readings(
            artifact,
            frame,
            window_size_s=payload.window_size_s,
            capture_id="api_request",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return NILMPredictResponse(
        feature_set_version=result["feature_set_version"],
        window_size_s=result["window_size_s"],
        classes=result["classes"],
        windows=[
            NILMWindowPrediction(**prediction)
            for prediction in result["predictions"]
        ],
    )


def get_model_card() -> dict:
    metadata_path = _resolve_metadata_path()
    if not metadata_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NILM metadata file not found. Train the model first.",
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {
        "version": "nilm_v1",
        "model_type": "smart-plug appliance signature classifier",
        "feature_set": metadata.get("feature_set_version"),
        "window_size_s": metadata.get("window_size_s"),
        "n_classes": metadata.get("n_classes"),
        "classes": metadata.get("classes", []),
        "train_samples": metadata.get("train_samples"),
        "test_samples": metadata.get("test_samples"),
        "total_feature_windows": metadata.get("total_feature_windows"),
        "test_accuracy": metadata.get("test_accuracy"),
        "cv_mean_accuracy": metadata.get("cv_mean_accuracy"),
        "cv_std_accuracy": metadata.get("cv_std_accuracy"),
        "top_feature_importance": metadata.get("top_feature_importance", [])[:8],
        "limitation": metadata.get(
            "notes",
            "This model classifies smart-plug appliance signatures and is not yet aggregate household disaggregation.",
        ),
    }


def _normalize_importance_rows(rows: list[dict], score_key: str) -> list[dict]:
    normalized = []
    for row in rows:
        feature = row.get("feature")
        if not feature:
            continue
        score = row.get(score_key, row.get("importance", 0.0))
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0
        normalized.append({"feature": feature, "mean_abs_shap": score})
    return normalized


def get_shap_importance() -> dict:
    shap_path = _resolve_shap_path()
    if shap_path.exists():
        payload = json.loads(shap_path.read_text(encoding="utf-8"))
        return {
            "source": "shap",
            "model": payload.get("model"),
            "features": payload.get("features"),
            "sample_size": payload.get("sample_size"),
            "feature_importance": _normalize_importance_rows(
                payload.get("feature_importance", []),
                "mean_abs_shap",
            ),
        }

    metadata_path = _resolve_metadata_path()
    if not metadata_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NILM metadata file not found. Train the model first.",
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {
        "source": "model_feature_importance",
        "sample_size": metadata.get("total_feature_windows"),
        "message": "SHAP importance artifact not found. Run ml/explain.py to generate ml/results/shap_importance.json.",
        "feature_importance": _normalize_importance_rows(
            metadata.get("top_feature_importance", []),
            "importance",
        ),
    }
