"""SupplyChainAI — FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, shipments, fleet, predict, optimize, simulate, copilot, metrics
from services.data_service import DataService
from services.ml_service import MLService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("Starting SupplyChainAI backend...")
    try:
        DataService.initialize()
        logger.info("Data service initialized.")
        MLService.initialize()
        logger.info("ML service initialized.")
        # Precompute risk scores for all shipments (batch — fast)
        DataService.build_risk_cache()
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise
    yield
    logger.info("Shutting down SupplyChainAI backend.")


app = FastAPI(
    title="SupplyChainAI API",
    description="Agentic Supply Chain Risk & Fleet Optimization Platform",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(shipments.router, prefix="/api", tags=["shipments"])
app.include_router(fleet.router, prefix="/api", tags=["fleet"])
app.include_router(predict.router, prefix="/api", tags=["predict"])
app.include_router(optimize.router, prefix="/api", tags=["optimize"])
app.include_router(simulate.router, prefix="/api", tags=["simulate"])
app.include_router(copilot.router, prefix="/api", tags=["copilot"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
