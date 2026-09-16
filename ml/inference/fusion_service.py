"""
Multimodal Fusion and Operational Dynamic Risk Service.
Uttarakhand Landslide Intelligence Platform.
"""

import logging
from typing import Any, Dict, Optional
import numpy as np

from ml.inference.config import settings
from ml.inference.feature_service import feature_service
from ml.inference.model_loader import container
from ml.inference.swin_service import swin_service

logger = logging.getLogger("ml.inference.fusion_service")


class FusionService:
    """Combines static-visual ML with causal dynamic rainfall triggers."""

    def __init__(self):
        self.w_xgb = settings.FROZEN_W_XGB
        self.w_swin = settings.FROZEN_W_SWIN

    def assess_risk(
        self,
        latitude: float,
        longitude: float,
        timestamp: str,
        rainfall_weight: Optional[float] = None,
        combination_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multimodal risk assessment for a coordinate and timestamp.
        """
        w_rain = settings.DEFAULT_RAINFALL_WEIGHT if rainfall_weight is None else float(rainfall_weight)
        mode = (combination_mode or settings.DEFAULT_COMBINATION_MODE).lower()

        # 1. Branch 1: Static Terrain / Environmental Susceptibility (XGBoost)
        p_xgb, raw_features = feature_service.extract_features_and_predict(latitude, longitude)

        # 2. Branch 2: Satellite Visual Evidence Risk (Swin Transformer)
        p_swin, patch_path = swin_service.predict_visual_risk(latitude, longitude)

        # 3. Static-Visual Late Fusion (Frozen 0.38 / 0.62)
        static_visual_score = float(np.clip(self.w_xgb * p_xgb + self.w_swin * p_swin, 0.0, 1.0))

        # 4. Dynamic Hydrometeorological Triggering (CHIRPS Causal Rainfall Engine)
        rain_result = container.rainfall_engine.get_dynamic_rainfall_risk(latitude, longitude, timestamp)
        s_rain = float(rain_result.get("dynamic_rainfall_trigger_score", 0.0))
        trigger_ind = str(rain_result.get("trigger_indicator", "LOW_STRESS"))

        # 5. Operational Integrated Risk Score (Decision Support Heuristic)
        if mode == "multiplicative":
            raw_op = static_visual_score * (1.0 + w_rain * s_rain)
            op_score = float(round(np.clip(raw_op, 0.0, 1.0), 6))
        elif mode == "weighted":
            raw_op = (1.0 - w_rain) * static_visual_score + w_rain * s_rain
            op_score = float(round(np.clip(raw_op, 0.0, 1.0), 6))
        else:
            raise ValueError(f"Unsupported combination mode: {mode}")

        # 6. Operational Risk Level Categorization (LOW, MEDIUM, HIGH, CRITICAL)
        if op_score < settings.THRESHOLD_LOW:
            risk_level = "LOW"
        elif op_score < settings.THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
        elif op_score < settings.THRESHOLD_HIGH:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        max_daily = float(rain_result.get("maximum_daily_rainfall", rain_result.get("maximum_daily_rainfall_mm", 0.0)))

        return {
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "timestamp": timestamp,
            "xgboost_probability": round(p_xgb, 6),
            "swin_probability": round(p_swin, 6),
            "static_visual_fusion_score": round(static_visual_score, 6),
            "rainfall_3d_mm": round(float(rain_result.get("rainfall_3d_mm", 0.0)), 2),
            "rainfall_7d_mm": round(float(rain_result.get("rainfall_7d_mm", 0.0)), 2),
            "rainfall_14d_mm": round(float(rain_result.get("rainfall_14d_mm", 0.0)), 2),
            "rainfall_30d_mm": round(float(rain_result.get("rainfall_30d_mm", 0.0)), 2),
            "maximum_daily_rainfall_mm": round(max_daily, 2),
            "rainfall_anomaly": round(float(rain_result.get("rainfall_anomaly", 1.0)), 3),
            "dynamic_rainfall_trigger_score": round(s_rain, 4),
            "trigger_indicator": trigger_ind,
            "operational_landslide_risk_score": round(op_score, 6),
            "risk_level": risk_level,
            "model_version": settings.APP_VERSION,
            "status": "success",
        }


fusion_service = FusionService()
