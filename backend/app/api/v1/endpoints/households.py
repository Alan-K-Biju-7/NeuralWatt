from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_db
from app.core.security import get_current_user_id
from app.schemas.household import (
    HouseholdCreateRequest,
    HouseholdResponse,
    DeviceCreateRequest,
    DeviceResponse,
)
from app.services.household_service import (
    create_household,
    get_household_by_owner,
    get_household_by_id,
    add_device,
    format_household_response,
    format_device_response,
)

router = APIRouter(prefix="/households", tags=["Households"])


@router.post(
    "",
    response_model=HouseholdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_household(
    payload: HouseholdCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    household = await create_household(db, payload, user_id)
    return format_household_response(household)


@router.get("/me", response_model=HouseholdResponse)
async def get_my_household(
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    household = await get_household_by_owner(db, user_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No household found. Create one first.",
        )
    return format_household_response(household)


@router.post(
    "/{household_id}/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_device_to_household(
    household_id: str,
    payload: DeviceCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    device = await add_device(db, household_id, user_id, payload)
    return format_device_response(device)


@router.get(
    "/{household_id}/devices",
    response_model=list[DeviceResponse],
)
async def list_devices(
    household_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    household = await get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    if household.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this household",
        )
    return [format_device_response(d) for d in household.devices]
