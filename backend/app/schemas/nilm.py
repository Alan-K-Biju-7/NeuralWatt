from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class NILMReading(BaseModel):
    timestamp: datetime
    power_w: Optional[float] = Field(
        None,
        ge=0,
        le=15000,
        description="Active power in watts",
    )
    voltage_v: Optional[float] = Field(
        None,
        ge=0,
        le=280,
        description="AC voltage in volts",
    )
    current_a: Optional[float] = Field(
        None,
        ge=0,
        le=80,
        description="Current in amperes",
    )
    watts: Optional[float] = Field(
        None,
        ge=0,
        le=15000,
        description="Legacy alias for power_w",
    )
    voltage: Optional[float] = Field(
        None,
        ge=0,
        le=280,
        description="Legacy alias for voltage_v",
    )
    current: Optional[float] = Field(
        None,
        ge=0,
        le=80,
        description="Legacy alias for current_a",
    )

    @model_validator(mode="after")
    def normalize_legacy_fields(self) -> "NILMReading":
        if self.power_w is None:
            self.power_w = self.watts
        if self.voltage_v is None:
            self.voltage_v = self.voltage
        if self.current_a is None:
            self.current_a = self.current
        if self.power_w is None:
            raise ValueError("power_w is required")
        return self


class NILMPredictRequest(BaseModel):
    readings: List[NILMReading] = Field(
        ...,
        min_length=3,
        description="Chronological readings to classify into appliance windows",
    )
    window_size_s: int = Field(
        30,
        ge=5,
        le=300,
        description="Prediction window size in seconds",
    )


class NILMWindowPrediction(BaseModel):
    window_index: int
    predicted_appliance: str
    confidence: float = Field(..., ge=0, le=1)
    probabilities: Dict[str, float]


class NILMPredictResponse(BaseModel):
    model_version: str = "nilm_v1"
    feature_set_version: Optional[str] = None
    window_size_s: int
    classes: List[str]
    windows: List[NILMWindowPrediction]
