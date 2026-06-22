from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.forecast_service import hourly_energy_frame
from app.services.nilm_service import get_model_card, get_shap_importance
from app.services.recommendation_service import evaluate_rules, summarize_readings
from ml.forecast import build_forecast_feature_frame


def _hourly_readings(count: int = 26) -> pd.DataFrame:
    start = datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc)
    return pd.DataFrame(
        {
            "timestamp": [start + timedelta(hours=index) for index in range(count)],
            "energy_kwh": [0.2 for _ in range(count)],
            "power_w": [200 for _ in range(count)],
        }
    )


def test_hourly_energy_frame_prepares_prophet_columns():
    hourly = hourly_energy_frame(_hourly_readings())

    assert list(hourly.columns) == ["ds", "y"]
    assert len(hourly) == 26
    assert round(hourly["y"].sum(), 4) == 5.2


def test_forecast_feature_frame_adds_time_and_hw_features():
    hourly = hourly_energy_frame(_hourly_readings(48))
    features = build_forecast_feature_frame(hourly)

    expected = {
        "sin_hour",
        "cos_hour",
        "sin_weekday",
        "cos_weekday",
        "hw_level",
        "hw_trend",
        "hw_seasonal",
        "hw_residual",
    }
    assert expected.issubset(features.columns)
    assert len(features) == len(hourly)


def test_recommendation_summary_calculates_peak_window_energy():
    readings = _hourly_readings()

    summary = summarize_readings(readings)

    assert summary["reading_count"] == 26
    assert summary["total_kwh"] == 5.2
    assert summary["peak_kwh"] > 0
    assert summary["estimated_daily_cost"] > 0


def test_recommendation_rules_raise_high_usage_and_peak_shift():
    recommendations = evaluate_rules(
        {
            "total_kwh": 10.0,
            "peak_kwh": 4.0,
            "average_power_w": 450.0,
            "max_power_w": 2200.0,
            "reading_count": 500,
            "estimated_daily_cost": 90.0,
        }
    )

    ids = {item["id"] for item in recommendations}
    assert "high_daily_energy" in ids
    assert "peak_hour_shift" in ids
    assert "high_power_spike" in ids


def test_recommendation_rules_include_stable_fallback():
    recommendations = evaluate_rules(
        {
            "total_kwh": 2.0,
            "peak_kwh": 0.2,
            "average_power_w": 80.0,
            "max_power_w": 400.0,
            "reading_count": 200,
            "estimated_daily_cost": 15.0,
        }
    )

    assert recommendations == [
        {
            "id": "normal_usage",
            "title": "Usage pattern looks stable",
            "message": "No major saving rule fired in the latest 24-hour window.",
            "severity": "low",
            "savings_hint": "Continue monitoring appliance-level trends",
        }
    ]


def test_nilm_model_card_reads_current_metadata():
    card = get_model_card()

    assert card["version"] == "nilm_v1"
    assert card["n_classes"] >= 5
    assert "washing_machine" in card["classes"]


def test_nilm_shap_importance_returns_ranked_features():
    importance = get_shap_importance()

    assert importance["source"] in {"shap", "model_feature_importance"}
    assert importance["feature_importance"]
    assert "feature" in importance["feature_importance"][0]
    assert "mean_abs_shap" in importance["feature_importance"][0]
