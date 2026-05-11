from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from app.schemas.household import DeviceType


class DeviceDocument:
    def __init__(
        self,
        name: str,
        device_type: DeviceType,
        rated_power_watts: float,
        location: Optional[str] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.name = name
        self.device_type = device_type
        self.rated_power_watts = rated_power_watts
        self.location = location
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "name": self.name,
            "device_type": self.device_type,
            "rated_power_watts": self.rated_power_watts,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "DeviceDocument":
        return DeviceDocument(
            _id=data.get("_id"),
            name=data["name"],
            device_type=data["device_type"],
            rated_power_watts=data["rated_power_watts"],
            location=data.get("location"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
        )


class HouseholdDocument:
    def __init__(
        self,
        owner_id: str,
        name: str,
        address: Optional[str] = None,
        area_sqft: Optional[float] = None,
        num_occupants: Optional[int] = None,
        devices: Optional[List[DeviceDocument]] = None,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.owner_id = owner_id
        self.name = name
        self.address = address
        self.area_sqft = area_sqft
        self.num_occupants = num_occupants
        self.devices = devices or []
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "owner_id": self.owner_id,
            "name": self.name,
            "address": self.address,
            "area_sqft": self.area_sqft,
            "num_occupants": self.num_occupants,
            "devices": [d.to_dict() for d in self.devices],
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "HouseholdDocument":
        return HouseholdDocument(
            _id=data.get("_id"),
            owner_id=data["owner_id"],
            name=data["name"],
            address=data.get("address"),
            area_sqft=data.get("area_sqft"),
            num_occupants=data.get("num_occupants"),
            devices=[DeviceDocument.from_dict(d) for d in data.get("devices", [])],
            created_at=data.get("created_at"),
        )
