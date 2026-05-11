from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class ReadingDocument:
    def __init__(
        self,
        device_id: str,
        household_id: str,
        watts: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.household_id = household_id
        self.watts = watts
        self.voltage = voltage
        self.current = current
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "device_id": self.device_id,
            "household_id": self.household_id,
            "watts": self.watts,
            "voltage": self.voltage,
            "current": self.current,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict) -> "ReadingDocument":
        return ReadingDocument(
            _id=data.get("_id"),
            device_id=data["device_id"],
            household_id=data["household_id"],
            watts=data["watts"],
            voltage=data.get("voltage"),
            current=data.get("current"),
            timestamp=data.get("timestamp"),
        )
