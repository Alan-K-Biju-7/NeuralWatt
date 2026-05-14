from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.schemas.reading import ReadingSource


class ReadingDocument:
    def __init__(
        self,
        device_id: str,
        household_id: str,
        power_w: float,
        voltage_v: Optional[float] = None,
        current_a: Optional[float] = None,
        energy_kwh: Optional[float] = None,
        frequency_hz: Optional[float] = None,
        power_factor: Optional[float] = None,
        source: ReadingSource | str = ReadingSource.UNKNOWN,
        timestamp: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.household_id = household_id
        self.power_w = power_w
        self.voltage_v = voltage_v
        self.current_a = current_a
        self.energy_kwh = energy_kwh
        self.frequency_hz = frequency_hz
        self.power_factor = power_factor
        self.source = ReadingSource(source)
        self.timestamp = timestamp or datetime.now(timezone.utc)

    @property
    def watts(self) -> float:
        return self.power_w

    @property
    def voltage(self) -> Optional[float]:
        return self.voltage_v

    @property
    def current(self) -> Optional[float]:
        return self.current_a

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "device_id": self.device_id,
            "household_id": self.household_id,
            "power_w": self.power_w,
            "voltage_v": self.voltage_v,
            "current_a": self.current_a,
            "energy_kwh": self.energy_kwh,
            "frequency_hz": self.frequency_hz,
            "power_factor": self.power_factor,
            "source": self.source.value,
            "watts": self.power_w,
            "voltage": self.voltage_v,
            "current": self.current_a,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict) -> "ReadingDocument":
        return ReadingDocument(
            _id=data.get("_id"),
            device_id=data["device_id"],
            household_id=data["household_id"],
            power_w=data.get("power_w", data.get("watts", 0)),
            voltage_v=data.get("voltage_v", data.get("voltage")),
            current_a=data.get("current_a", data.get("current")),
            energy_kwh=data.get("energy_kwh"),
            frequency_hz=data.get("frequency_hz"),
            power_factor=data.get("power_factor"),
            source=data.get("source", ReadingSource.UNKNOWN),
            timestamp=data.get("timestamp"),
        )
