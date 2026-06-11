from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import get_current_user_id
from app.db.mongodb import get_db
from app.services.recommendation_service import get_recommendations


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{household_id}")
async def household_recommendations(
    household_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_recommendations(db, household_id, user_id)
