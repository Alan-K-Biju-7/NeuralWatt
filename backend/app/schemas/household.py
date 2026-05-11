from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    AC = "ac"
    REFRIGERATOR = "refrigerator"
    WASHING_MACHINE = "washing_machine"
    WATER_HEATER = "water_heater"
    LIGHTING = "lighting"
    TV = "tv"
    COMPUTER = "computer"
    OTHER = "other"


class DeviceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    device_type: DeviceType
    rated_power_watts: float = Field(..., gt=0, description="Rated power in watts")
    location: Optional[str] = Field(None, max_length=100)


class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: DeviceType
    rated_power_watts: float
    location: Optional[str]
    is_active: bool
    created_at: datetime


class HouseholdCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    area_sqft: Optional[float] = Field(None, gt=0)
    num_occupants: Optional[int] = Field(None, ge=1)


class HouseholdResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    address: Optional[str]
    area_sqft: Optional[float]
    num_occupants: Optional[int]
    devices: List[DeviceResponse] = []
    created_at: datetime
