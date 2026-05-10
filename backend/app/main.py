from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.mongodb import connect_db, close_db
from app.api.v1.router import api_router
import logging

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    logger.info("NeuralWatt backend started ✅")
    yield
    await close_db()
    logger.info("NeuralWatt backend shut down 🔴")


app = FastAPI(
    title="NeuralWatt API",
    description="Smart energy monitoring and anomaly detection backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "env": settings.app_env, "version": "0.1.0"}
