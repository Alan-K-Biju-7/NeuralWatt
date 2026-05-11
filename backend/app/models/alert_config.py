from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.schemas.alert_config import SeverityThreshold


class AlertConfigDocument:
    def __init__(
        self,
        device_id: str,
        household_id: str,
        owner_id: str,
        severity_threshold: SeverityThreshold = SeverityThreshold.HIGH,
        email_enabled: bool = False,
        email_address: Optional[str] = None,
        webhook_enabled: bool = False,
        webhook_url: Optional[str] = None,
        _id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.household_id = household_id
        self.owner_id = owner_id
        self.severity_threshold = severity_threshold
        self.email_enabled = email_enabled
        self.email_address = email_address
        self.webhook_enabled = webhook_enabled
        self.webhook_url = webhook_url
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "device_id": self.device_id,
            "household_id": self.household_id,
            "owner_id": self.owner_id,
            "severity_threshold": self.severity_threshold.value,
            "email_enabled": self.email_enabled,
            "email_address": self.email_address,
            "webhook_enabled": self.webhook_enabled,
            "webhook_url": self.webhook_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlertConfigDocument":
        return cls(
            _id=data.get("_id"),
            device_id=data["device_id"],
            household_id=data["household_id"],
            owner_id=data["owner_id"],
            severity_threshold=SeverityThreshold(data.get("severity_threshold", "high")),
            email_enabled=data.get("email_enabled", False),
            email_address=data.get("email_address"),
            webhook_enabled=data.get("webhook_enabled", False),
            webhook_url=data.get("webhook_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
