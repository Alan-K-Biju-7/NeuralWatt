from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.nilm import NILMPredictRequest, NILMPredictResponse
from app.services.nilm_service import predict_nilm_windows


router = APIRouter(prefix="/nilm", tags=["NILM"])


@router.post("/predict", response_model=NILMPredictResponse)
async def predict_nilm(
    payload: NILMPredictRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Predict appliance windows from submitted energy readings."""
    return predict_nilm_windows(payload)
