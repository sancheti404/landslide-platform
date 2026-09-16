"""
FastAPI Inference Application for Uttarakhand Landslide Intelligence Platform.
Step 42 — End-to-End System Integration.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ml.inference.config import settings
from ml.inference.fusion_service import fusion_service
from ml.inference.model_loader import container
from ml.inference.schemas import ErrorResponse, HealthResponse, RiskAssessmentRequest, RiskAssessmentResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ml.inference.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes models once during startup and cleans up on shutdown."""
    logger.info("Initializing %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    t0 = time.time()
    try:
        container.load_all()
        elapsed = time.time() - t0
        logger.info("Service initialized successfully in %.2f seconds.", elapsed)
    except Exception as e:
        logger.error("FATAL: Failed to load model artifacts: %s", e, exc_info=True)
        raise RuntimeError(f"Model startup failed: {e}") from e

    yield

    logger.info("Shutting down ML inference service...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Operational multimodal landslide risk inference combining static terrain susceptibility, satellite optical evidence, and dynamic rainfall triggering.",
    lifespan=lifespan,
)

# Enable CORS for Spring Boot backend and local web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Catches domain validation errors and out-of-bounds geographic requests."""
    msg = str(exc)
    code = "UNSUPPORTED_LOCATION" if ("outside" in msg.lower() or "coverage" in msg.lower()) else "INVALID_REQUEST"
    logger.warning("Validation rejected [%s]: %s", code, msg)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            status="error",
            error_code=code,
            message=msg,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and returns structured JSON without exposing internal stack traces."""
    logger.error("Unhandled inference error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            error_code="INTERNAL_INFERENCE_ERROR",
            message="An error occurred while evaluating the multimodal risk model.",
            details={"error_type": exc.__class__.__name__},
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Returns service readiness, loaded models status, and hardware device."""
    info = container.get_health_status()
    return HealthResponse(
        status=info["status"],
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        models_loaded=info["models_loaded"],
        device=info["device"],
        uptime_seconds=info["uptime_seconds"],
    )


@app.post("/risk/assess", response_model=RiskAssessmentResponse, tags=["Inference"])
async def assess_landslide_risk(request: RiskAssessmentRequest):
    """
    Evaluates real-time operational landslide risk for the given coordinates and timestamp.
    Combines:
      - XGBoost Static Terrain Susceptibility
      - Swin Transformer Sentinel-2 Visual Risk
      - Static-Visual Late Fusion (0.38 XGB + 0.62 Swin)
      - CHIRPS Causal Antecedent Rainfall Trigger Score
      - Operational Integrated Risk Score & Risk Level
    """
    # 1. Authoritative Operational Geospatial Envelope Validation
    if not (settings.MIN_LAT <= request.latitude <= settings.MAX_LAT and settings.MIN_LON <= request.longitude <= settings.MAX_LON):
        logger.warning(
            "Rejected coordinate (%.6f, %.6f) outside Uttarakhand operational envelope [%.2f–%.2f°N, %.2f–%.2f°E]",
            request.latitude, request.longitude, settings.MIN_LAT, settings.MAX_LAT, settings.MIN_LON, settings.MAX_LON
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                status="error",
                error_code="UNSUPPORTED_LOCATION",
                message="Selected coordinate is outside supported Uttarakhand operational coverage.",
                latitude=request.latitude,
                longitude=request.longitude,
            ).model_dump(),
        )

    t0 = time.time()
    result = fusion_service.assess_risk(
        latitude=request.latitude,
        longitude=request.longitude,
        timestamp=request.timestamp,
        rainfall_weight=request.rainfall_weight,
        combination_mode=request.combination_mode,
    )
    elapsed_ms = (time.time() - t0) * 1000.0
    logger.info("Risk assessed for (%.4f, %.4f) @ %s -> Score: %.4f [%s] in %.1f ms",
                request.latitude, request.longitude, request.timestamp,
                result["operational_landslide_risk_score"], result["risk_level"], elapsed_ms)
    return RiskAssessmentResponse(**result)
