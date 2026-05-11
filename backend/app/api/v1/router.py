from fastapi import APIRouter
from app.api.v1.endpoints import auth, households, readings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(households.router)
api_router.include_router(readings.router)
