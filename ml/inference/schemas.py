"""
Pydantic Request and Response Schemas for the ML Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class RiskAssessmentRequest(BaseModel):
    """Payload for risk assessment queries."""
    latitude: float = Field(..., description="Latitude in decimal degrees (e.g., 30.529505)")
    longitude: float = Field(..., description="Longitude in decimal degrees (e.g., 79.085957)")
    timestamp: str = Field(..., description="Target assessment date in ISO-8601 or YYYY-MM-DD format")
    rainfall_weight: Optional[float] = Field(0.50, ge=0.0, le=2.0, description="Multiplier for dynamic rainfall trigger")
    combination_mode: Optional[str] = Field("multiplicative", description="Combination mode: 'multiplicative' or 'weighted'")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        clean = v.strip().split("T")[0].split(" ")[0]
        parts = clean.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid timestamp format '{v}'. Expected YYYY-MM-DD or ISO-8601.")
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1980 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError
        except Exception:
            raise ValueError(f"Invalid calendar date values in timestamp '{v}'.")
        return clean


class RiskAssessmentResponse(BaseModel):
    """Comprehensive structured response matching all requirements."""
    latitude: float
    longitude: float
    timestamp: str

    # ML Static-Visual Signals (calibrated posterior probabilities)
    xgboost_probability: float = Field(..., ge=0.0, le=1.0)
    swin_probability: float = Field(..., ge=0.0, le=1.0)
    static_visual_fusion_score: float = Field(..., ge=0.0, le=1.0)

    # Dynamic Hydrometeorological Indicators (causal antecedent CHIRPS rainfall)
    rainfall_3d_mm: float = Field(..., ge=0.0)
    rainfall_7d_mm: float = Field(..., ge=0.0)
    rainfall_14d_mm: float = Field(..., ge=0.0)
    rainfall_30d_mm: float = Field(..., ge=0.0)
    maximum_daily_rainfall_mm: float = Field(..., ge=0.0)
    rainfall_anomaly: float = Field(..., ge=0.0)
    dynamic_rainfall_trigger_score: float = Field(..., ge=0.0, le=1.0)
    trigger_indicator: str

    # Integrated Operational Risk Heuristic
    operational_landslide_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str

    # Operational Metadata
    model_version: str
    status: str = "success"


class HealthResponse(BaseModel):
    """System health and model readiness status."""
    status: str
    app_name: str
    version: str
    models_loaded: Dict[str, bool]
    device: str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Structured error payload for client safety."""
    status: str
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
