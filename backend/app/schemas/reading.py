from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReadingCreateRequest(BaseModel):
    watts: float = Field(..., gt=0, description="Power consumption in watts")
    voltage: Optional[float] = Field(None, gt=0, description="Voltage in volts")
    current: Optional[float] = Field(None, gt=0, description="Current in amperes")
    timestamp: Optional[datetime] = Field(
        None, description="Reading timestamp (defaults to now if omitted)"
    )


class ReadingResponse(BaseModel):
    id: str
    device_id: str
    household_id: str
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
