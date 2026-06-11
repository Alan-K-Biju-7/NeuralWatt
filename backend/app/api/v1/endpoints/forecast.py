from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import get_current_user_id
from app.db.mongodb import get_db
from app.services.forecast_service import get_readings_for_forecast, run_forecast


router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/{household_id}")
async def forecast_household(
    household_id: str,
    days: int = Query(30, ge=2, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    readings = await get_readings_for_forecast(db, household_id, user_id, days)
    if readings.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings available for this household",
        )

    try:
        points = run_forecast(readings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "household_id": household_id,
        "history_days": days,
        "horizon_hours": 24,
        "forecast": points,
    }
