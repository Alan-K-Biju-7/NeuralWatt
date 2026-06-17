from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.nilm import NILMPredictRequest, NILMPredictResponse
from app.services.nilm_service import (
    get_model_card,
    get_shap_importance,
    predict_nilm_windows,
)


router = APIRouter(prefix="/nilm", tags=["NILM"])


@router.post("/predict", response_model=NILMPredictResponse)
async def predict_nilm(
    payload: NILMPredictRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Predict appliance windows from submitted energy readings."""
    return predict_nilm_windows(payload)


@router.get("/model-card")
async def nilm_model_card(user_id: str = Depends(get_current_user_id)):
    """Return the trained NILM model metadata used by the dashboard."""
    return get_model_card()


@router.get("/shap")
async def nilm_shap_importance(user_id: str = Depends(get_current_user_id)):
    """Return SHAP feature importance, or model importance until SHAP is generated."""
    return get_shap_importance()
