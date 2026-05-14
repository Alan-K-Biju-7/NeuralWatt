import pytest
from pydantic import ValidationError

from app.schemas.reading import ReadingCreateRequest, ReadingSource


def test_reading_schema_accepts_canonical_payload():
    reading = ReadingCreateRequest(
        power_w=500,
        voltage_v=230,
        current_a=2.17,
        energy_kwh=0.01,
        frequency_hz=50,
        power_factor=0.95,
        source="esp32",
    )

    assert reading.power_w == 500
    assert reading.source == ReadingSource.ESP32


def test_reading_schema_backfills_legacy_payload():
    reading = ReadingCreateRequest(watts=250, voltage=229, current=1.09)

    assert reading.power_w == 250
    assert reading.voltage_v == 229
    assert reading.current_a == 1.09


def test_reading_schema_rejects_unsafe_voltage():
    with pytest.raises(ValidationError):
        ReadingCreateRequest(power_w=100, voltage_v=400)
