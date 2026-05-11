from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, model_validator


class SeverityThreshold(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class AlertConfigCreateRequest(BaseModel):
    severity_threshold: SeverityThreshold = SeverityThreshold.HIGH
    email_enabled: bool = False
    email_address: Optional[EmailStr] = None
    webhook_enabled: bool = False
    webhook_url: Optional[HttpUrl] = None

    @model_validator(mode="after")
    def validate_channels(self) -> "AlertConfigCreateRequest":
        if self.email_enabled and not self.email_address:
            raise ValueError("email_address is required when email_enabled is true")
        if self.webhook_enabled and not self.webhook_url:
            raise ValueError("webhook_url is required when webhook_enabled is true")
        if not self.email_enabled and not self.webhook_enabled:
            raise ValueError("At least one notification channel must be enabled")
        return self


class AlertConfigUpdateRequest(BaseModel):
    severity_threshold: Optional[SeverityThreshold] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[EmailStr] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[HttpUrl] = None


class AlertConfigResponse(BaseModel):
    id: str
    device_id: str
    household_id: str
    severity_threshold: SeverityThreshold
    email_enabled: bool
    email_address: Optional[str] = None
    webhook_enabled: bool
    webhook_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
