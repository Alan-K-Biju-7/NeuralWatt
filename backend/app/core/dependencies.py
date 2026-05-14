from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.mongodb import get_db
from app.services.household_service import get_household_by_id


optional_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ReadingIngestPrincipal:
    user_id: Optional[str] = None
    household_id: Optional[str] = None
    device_id: Optional[str] = None
    auth_type: str = "jwt"


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> Optional[str]:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def verify_reading_ingest_auth(
    household_id: str,
    device_id: str,
    x_device_key: str | None = Header(None, alias="X-Device-Key"),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ReadingIngestPrincipal:
    if x_device_key:
        household = await get_household_by_id(db, household_id)
        if not household:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Household not found",
            )
        for device in household.devices:
            if str(device._id) == device_id and device.device_key == x_device_key:
                return ReadingIngestPrincipal(
                    household_id=household_id,
                    device_id=device_id,
                    auth_type="device_key",
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device key",
        )

    if user_id:
        return ReadingIngestPrincipal(user_id=user_id, auth_type="jwt")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Bearer token or X-Device-Key",
    )
