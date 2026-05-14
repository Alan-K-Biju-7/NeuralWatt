from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReadingSource(str, Enum):
    SIMULATOR = "simulator"
    ESP32 = "esp32"
    PZEM_004T = "pzem_004t"
    MANUAL = "manual"
    BACKFILL = "backfill"
    UNKNOWN = "unknown"


class ReadingCreateRequest(BaseModel):
    power_w: Optional[float] = Field(
        None, ge=0, le=15000, description="Active power in watts"
    )
    voltage_v: Optional[float] = Field(
        None, ge=180, le=260, description="AC voltage in volts"
    )
    current_a: Optional[float] = Field(
        None, ge=0, le=60, description="Current in amperes"
    )
    energy_kwh: Optional[float] = Field(
        None, ge=0, description="Cumulative or interval energy in kWh"
    )
    frequency_hz: Optional[float] = Field(
        None, ge=45, le=65, description="AC frequency in Hz"
    )
    power_factor: Optional[float] = Field(
        None, ge=0, le=1, description="Power factor from 0.00 to 1.00"
    )
    source: ReadingSource = ReadingSource.UNKNOWN
    watts: Optional[float] = Field(
        None, ge=0, le=15000, description="Legacy alias for power_w"
    )
    voltage: Optional[float] = Field(
        None, gt=0, description="Legacy alias for voltage_v"
    )
    current: Optional[float] = Field(
        None, ge=0, description="Legacy alias for current_a"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Reading timestamp (defaults to now if omitted)"
    )

    @model_validator(mode="after")
    def normalize_legacy_fields(self) -> "ReadingCreateRequest":
        if self.power_w is None:
            self.power_w = self.watts
        if self.voltage_v is None:
            self.voltage_v = self.voltage
        if self.current_a is None:
            self.current_a = self.current
        if self.power_w is None:
            raise ValueError("power_w is required")
        if not 0 <= self.power_w <= 15000:
            raise ValueError("power_w must be between 0 and 15000")
        if self.voltage_v is not None and not 180 <= self.voltage_v <= 260:
            raise ValueError("voltage_v must be between 180 and 260")
        if self.current_a is not None and not 0 <= self.current_a <= 60:
            raise ValueError("current_a must be between 0 and 60")
        return self


class ReadingResponse(BaseModel):
    id: str
    device_id: str
    household_id: str
    power_w: float
    voltage_v: Optional[float]
    current_a: Optional[float]
    energy_kwh: Optional[float]
    frequency_hz: Optional[float]
    power_factor: Optional[float]
    source: ReadingSource
    watts: float
    voltage: Optional[float]
    current: Optional[float]
    timestamp: datetime


class ReadingStatsResponse(BaseModel):
    device_id: str
    count: int
    avg_watts: float
    min_watts: float
    max_watts: float
    total_kwh: float
    from_timestamp: datetime
    to_timestamp: datetime


class ReadingListResponse(BaseModel):
    device_id: str
    readings: List[ReadingResponse]
    total: int
