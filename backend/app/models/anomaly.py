from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.schemas.anomaly import AnomalySeverity


class AnomalyDocument:
    def __init__(
        self,
        device_id: str,
        household_id: str,
        reading_id: str,
        watts: float,
        expected_watts: float,
        deviation_pct: float,
        severity: AnomalySeverity,
        message: str,
        detected_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.household_id = household_id
        self.reading_id = reading_id
        self.watts = watts
        self.expected_watts = expected_watts
        self.deviation_pct = deviation_pct
        self.severity = severity
        self.message = message
        self.detected_at = detected_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "device_id": self.device_id,
            "household_id": self.household_id,
            "reading_id": self.reading_id,
            "watts": self.watts,
            "expected_watts": self.expected_watts,
            "deviation_pct": self.deviation_pct,
            "severity": self.severity,
            "message": self.message,
            "detected_at": self.detected_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "AnomalyDocument":
        return AnomalyDocument(
            _id=data.get("_id"),
            device_id=data["device_id"],
            household_id=data["household_id"],
            reading_id=data["reading_id"],
            watts=data["watts"],
            expected_watts=data["expected_watts"],
            deviation_pct=data["deviation_pct"],
            severity=data["severity"],
            message=data["message"],
            detected_at=data.get("detected_at"),
        )
