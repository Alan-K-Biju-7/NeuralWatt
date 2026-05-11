from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_db
from app.core.security import get_current_user_id
from app.schemas.alert_config import (
    AlertConfigCreateRequest,
    AlertConfigUpdateRequest,
    AlertConfigResponse,
)
from app.services.alert_config_service import (
    create_alert_config,
    get_alert_config,
    update_alert_config,
    delete_alert_config,
    format_alert_config_response,
)

router = APIRouter(prefix="/households", tags=["Alert Configs"])


@router.post(
    "/{household_id}/devices/{device_id}/alert-config",
    response_model=AlertConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_config(
    household_id: str,
    device_id: str,
    payload: AlertConfigCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    config = await create_alert_config(db, household_id, device_id, user_id, payload)
    return format_alert_config_response(config)


@router.get(
    "/{household_id}/devices/{device_id}/alert-config",
    response_model=AlertConfigResponse,
)
async def get_config(
    household_id: str,
    device_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    config = await get_alert_config(db, household_id, device_id, user_id)
    return format_alert_config_response(config)


@router.patch(
    "/{household_id}/devices/{device_id}/alert-config",
    response_model=AlertConfigResponse,
)
async def update_config(
    household_id: str,
    device_id: str,
    payload: AlertConfigUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    config = await update_alert_config(db, household_id, device_id, user_id, payload)
    return format_alert_config_response(config)


@router.delete(
    "/{household_id}/devices/{device_id}/alert-config",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_config(
    household_id: str,
    device_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await delete_alert_config(db, household_id, device_id, user_id)
