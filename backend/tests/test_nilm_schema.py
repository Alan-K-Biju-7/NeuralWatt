from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.nilm import NILMPredictRequest, NILMReading


def _timestamp(offset_s: int = 0) -> datetime:
    return datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_s
    )


def test_nilm_reading_accepts_canonical_payload():
    reading = NILMReading(
        timestamp=_timestamp(),
        power_w=72.5,
        voltage_v=235.0,
        current_a=0.31,
    )

    assert reading.power_w == 72.5
    assert reading.voltage_v == 235.0
    assert reading.current_a == 0.31


def test_nilm_reading_backfills_legacy_payload():
    reading = NILMReading(timestamp=_timestamp(), watts=1400, voltage=230, current=6.1)

    assert reading.power_w == 1400
    assert reading.voltage_v == 230
    assert reading.current_a == 6.1


def test_nilm_request_requires_enough_readings():
    with pytest.raises(ValidationError):
        NILMPredictRequest(
            readings=[
                NILMReading(timestamp=_timestamp(), power_w=10),
                NILMReading(timestamp=_timestamp(5), power_w=12),
            ]
        )


def test_nilm_request_accepts_window_settings():
    payload = NILMPredictRequest(
        window_size_s=30,
        readings=[
            NILMReading(timestamp=_timestamp(), power_w=10),
            NILMReading(timestamp=_timestamp(5), power_w=12),
            NILMReading(timestamp=_timestamp(10), power_w=11),
        ],
    )

    assert payload.window_size_s == 30
    assert len(payload.readings) == 3
