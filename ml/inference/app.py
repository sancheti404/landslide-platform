"""
FastAPI Inference Application for Uttarakhand Landslide Intelligence Platform.
Step 42 — End-to-End System Integration.
"""

import json
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request, Response, status
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

# Request ID Correlation and Latency Logging Middleware
@app.middleware("http")
async def add_request_id_and_tracing(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    t_start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


# Enable CORS for Spring Boot backend and local web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Catches domain validation errors and out-of-bounds geographic requests."""
    msg = str(exc)
    code = "UNSUPPORTED_LOCATION" if ("outside" in msg.lower() or "coverage" in msg.lower()) else "INVALID_REQUEST"
    req_id = getattr(request.state, "request_id", "unknown")
    logger.warning("Validation rejected [%s] req_id=%s: %s", code, req_id, msg)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            status="error",
            error_code=code,
            message=msg,
        ).model_dump(),
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and returns structured JSON without exposing internal stack traces."""
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled inference error req_id=%s: %s", req_id, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            error_code="INTERNAL_INFERENCE_ERROR",
            message="An error occurred while evaluating the multimodal risk model.",
            details={"error_type": exc.__class__.__name__},
        ).model_dump(),
        headers={"X-Request-ID": req_id},
    )


@app.get("/health/live", tags=["Monitoring"])
async def health_live():
    """Liveness probe: verifies the process is responsive."""
    return {"status": "alive", "timestamp": time.time()}


@app.get("/health/ready", tags=["Monitoring"])
async def health_ready():
    """Readiness probe: verifies all ML models and spatial indexes are loaded and ready."""
    if not container.is_loaded:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "initializing", "message": "Model artifacts still loading."},
        )
    return {
        "status": "ready",
        "device": str(container.device),
        "models_loaded": container.get_health_status()["models_loaded"],
    }


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
async def assess_landslide_risk(assessment_request: RiskAssessmentRequest, http_request: Request):
    """
    Evaluates real-time operational landslide risk for the given coordinates and timestamp.
    Combines:
      - XGBoost Static Terrain Susceptibility
      - Swin Transformer Sentinel-2 Visual Risk
      - Static-Visual Late Fusion (0.38 XGB + 0.62 Swin)
      - CHIRPS Causal Antecedent Rainfall Trigger Score
      - Operational Integrated Risk Score & Risk Level
    """
    req_id = getattr(http_request.state, "request_id", "unknown")

    # 1. Authoritative Operational Geospatial Envelope Validation
    if not (settings.MIN_LAT <= assessment_request.latitude <= settings.MAX_LAT and settings.MIN_LON <= assessment_request.longitude <= settings.MAX_LON):
        logger.warning(
            "Rejected coordinate (%.6f, %.6f) outside Uttarakhand operational envelope [%.2f–%.2f°N, %.2f–%.2f°E] req_id=%s",
            assessment_request.latitude, assessment_request.longitude,
            settings.MIN_LAT, settings.MAX_LAT, settings.MIN_LON, settings.MAX_LON, req_id
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                status="error",
                error_code="UNSUPPORTED_LOCATION",
                message="Selected coordinate is outside supported Uttarakhand operational coverage.",
                latitude=assessment_request.latitude,
                longitude=assessment_request.longitude,
            ).model_dump(),
            headers={"X-Request-ID": req_id},
        )

    t0 = time.perf_counter()
    result = fusion_service.assess_risk(
        latitude=assessment_request.latitude,
        longitude=assessment_request.longitude,
        timestamp=assessment_request.timestamp,
        rainfall_weight=assessment_request.rainfall_weight,
        combination_mode=assessment_request.combination_mode,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # Structured JSON log entry
    log_entry = {
        "event": "risk_assessment",
        "request_id": req_id,
        "latitude": assessment_request.latitude,
        "longitude": assessment_request.longitude,
        "timestamp": assessment_request.timestamp,
        "status": "success",
        "total_ms": round(elapsed_ms, 2),
        "timings_ms": result.get("timings_ms", {}),
        "xgboost_probability": result["xgboost_probability"],
        "swin_probability": result["swin_probability"],
        "static_visual_fusion_score": result["static_visual_fusion_score"],
        "dynamic_rainfall_trigger_score": result["dynamic_rainfall_trigger_score"],
        "operational_landslide_risk_score": result["operational_landslide_risk_score"],
        "risk_level": result["risk_level"],
    }
    logger.info("STRUCTURED_LOG: %s", json.dumps(log_entry))

    return RiskAssessmentResponse(**result)

