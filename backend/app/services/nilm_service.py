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
