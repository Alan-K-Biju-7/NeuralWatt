from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_db
from app.core.security import get_current_user_id
from app.schemas.analytics import (
    DailyUsageResponse,
    HourlyUsageResponse,
    UsageReportResponse,
    CostEstimateResponse,
)
from app.services.analytics_service import (
    get_daily_usage,
    get_hourly_usage,
    get_usage_report,
    get_cost_estimate,
)

router = APIRouter(prefix="/households", tags=["Analytics"])


@router.get(
    "/{household_id}/devices/{device_id}/analytics/daily",
    response_model=DailyUsageResponse,
)
async def daily_usage(
    household_id: str,
    device_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of past days to analyse"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_daily_usage(db, household_id, device_id, user_id, days)


@router.get(
    "/{household_id}/devices/{device_id}/analytics/hourly",
    response_model=HourlyUsageResponse,
)
async def hourly_usage(
    household_id: str,
    device_id: str,
    days: int = Query(7, ge=1, le=90, description="Lookback window in days"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_hourly_usage(db, household_id, device_id, user_id, days)


@router.get(
    "/{household_id}/devices/{device_id}/analytics/report",
    response_model=UsageReportResponse,
)
async def usage_report(
    household_id: str,
    device_id: str,
    period: str = Query("monthly", enum=["weekly", "monthly"], description="Report period"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_usage_report(db, household_id, device_id, user_id, period)


@router.get(
    "/{household_id}/devices/{device_id}/analytics/cost",
    response_model=CostEstimateResponse,
)
async def cost_estimate(
    household_id: str,
    device_id: str,
    days: int = Query(30, ge=1, le=365, description="Days to calculate cost over"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_cost_estimate(db, household_id, device_id, user_id, days)
