from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class UserDocument:
    """Represents a user document in MongoDB"""

    def __init__(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.email = email
        self.hashed_password = hashed_password
        self.full_name = full_name
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "UserDocument":
        return UserDocument(
            _id=data.get("_id"),
            email=data["email"],
            hashed_password=data["hashed_password"],
            full_name=data["full_name"],
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
        )
