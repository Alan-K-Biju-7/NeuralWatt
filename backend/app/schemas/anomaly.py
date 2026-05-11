from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyResponse(BaseModel):
    id: str
    device_id: str
    household_id: str
    reading_id: str
    watts: float
    expected_watts: float
    deviation_pct: float
    severity: AnomalySeverity
    detected_at: datetime
    message: str


class AnomalyListResponse(BaseModel):
    device_id: str
    anomalies: List[AnomalyResponse]
    total: int


class BaselineResponse(BaseModel):
    device_id: str
    avg_watts: float
    std_dev: float
    sample_count: int
    computed_at: datetime
