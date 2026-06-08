from fastapi import APIRouter
from app.api.v1.endpoints import (
    alert_configs,
    analytics,
    anomalies,
    auth,
    households,
    nilm,
    readings,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(households.router)
api_router.include_router(readings.router)
api_router.include_router(anomalies.router)
api_router.include_router(alert_configs.router)
api_router.include_router(analytics.router)
api_router.include_router(nilm.router)
