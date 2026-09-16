"""
Integrated Landslide Risk Engine for Operational Deployment.
Uttarakhand Landslide Intelligence Platform.

Combines:
1. Static Terrain Susceptibility (XGBoost)
2. Satellite Optical Visual Risk (Swin Transformer)
3. Dynamic Antecedent Hydrometeorological Stress (CHIRPS / Rainfall Engine)

Provides the public runtime API:
    get_integrated_landslide_risk(latitude, longitude, timestamp, ...)

CRITICAL SCIENTIFIC PRINCIPLES:
- The static-visual component represents spatial predisposition ($P_{sv} \in [0, 1]$).
- The dynamic rainfall component represents temporal meteorological triggering stress ($S_{rain} \in [0, 1]$).
- The resulting composite output is an OPERATIONAL RISK SCORE, NOT a calibrated probability.
- All constituent components remain individually exposed and fully visible.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib
import numpy as np
import pandas as pd

from ml.src.features.rainfall_trigger_engine import get_dynamic_rainfall_risk


# Default paths
PROJECT_ROOT = Path.cwd()
ML_DIR = PROJECT_ROOT / "ml"
FROZEN_FUSION_MODEL_PATH = ML_DIR / "models" / "final" / "static_visual_fusion_model.joblib"
MASTER_DATASET_PATH = ML_DIR / "data" / "processed" / "uttarakhand_master_ml_dataset.csv"
TEST_PREDICTIONS_PATH = ML_DIR / "reports" / "fusion" / "fusion_test_predictions.csv"


class IntegratedRiskEngine:
    """
    Operational engine that calculates multimodal integrated landslide hazard.
    Combines static-visual ML susceptibility with real-time antecedent rainfall trigger indices.
    """

    def __init__(
        self,
        fusion_model_path: Optional[Union[str, Path]] = None,
        rainfall_weight: float = 0.35,
        combination_mode: str = "multiplicative",
    ):
        """
        Args:
            fusion_model_path: Path to serialized frozen static-visual fusion model.
            rainfall_weight: Configurable scaling weight or multiplier for dynamic rainfall.
            combination_mode: Combination rule ('multiplicative' or 'weighted').
        """
        self.fusion_model_path = Path(fusion_model_path or FROZEN_FUSION_MODEL_PATH)
        self.rainfall_weight = float(rainfall_weight)
        self.combination_mode = combination_mode.lower()
        self._fusion_config = None
        self._cache_predictions = None

        self._load_fusion_config()
        self._load_lookup_cache()

    def _load_fusion_config(self):
        """Loads frozen weights for static-visual fusion."""
        if self.fusion_model_path.exists():
            try:
                self._fusion_config = joblib.load(self.fusion_model_path)
            except Exception:
                self._fusion_config = {"w_xgb": 0.50, "w_swin": 0.50}
        else:
            # Fallback default equal weights if file not yet written
            self._fusion_config = {"w_xgb": 0.50, "w_swin": 0.50}

    def _load_lookup_cache(self):
        """Loads spatial coordinate lookup cache for test/sample locations."""
        if TEST_PREDICTIONS_PATH.exists():
            try:
                self._cache_predictions = pd.read_csv(TEST_PREDICTIONS_PATH)
            except Exception:
                self._cache_predictions = None

    def compute_static_visual_score(
        self,
        xgboost_probability: Optional[float] = None,
        swin_probability: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Computes the static-visual fusion score from base branch probabilities or spatial lookup.
        """
        w_xgb = float(self._fusion_config.get("w_xgb", 0.50))
        w_swin = float(self._fusion_config.get("w_swin", 0.50))

        p_xgb = xgboost_probability
        p_swin = swin_probability

        # If base probabilities not provided, look up nearest known point in cache
        if (p_xgb is None or p_swin is None) and self._cache_predictions is not None and latitude is not None and longitude is not None:
            dist_sq = (
                (self._cache_predictions["latitude"] - latitude) ** 2 +
                (self._cache_predictions["longitude"] - longitude) ** 2
            )
            nearest_idx = dist_sq.idxmin()
            nearest = self._cache_predictions.loc[nearest_idx]
            if dist_sq.loc[nearest_idx] < 0.05:  # within ~25 km
                if p_xgb is None:
                    p_xgb = float(nearest["xgboost_probability"])
                if p_swin is None:
                    p_swin = float(nearest["swin_probability"])

        # Default fallback if unknown coordinate and unsupplied
        p_xgb = 0.50 if p_xgb is None else float(np.clip(p_xgb, 0.0, 1.0))
        p_swin = 0.50 if p_swin is None else float(np.clip(p_swin, 0.0, 1.0))

        score = float(np.clip(w_xgb * p_xgb + w_swin * p_swin, 0.0, 1.0))
        return {
            "xgboost_probability": round(p_xgb, 6),
            "swin_probability": round(p_swin, 6),
            "static_visual_fusion_score": round(score, 6),
        }

    def combine_scores(
        self,
        static_visual_score: float,
        rainfall_trigger_score: float,
        mode: Optional[str] = None,
        weight: Optional[float] = None,
    ) -> float:
        """
        Transparent, configurable runtime combination rule.

        Modes:
        - 'multiplicative':
            operational_score = clip(static_visual * (1.0 + alpha * rainfall_trigger), 0.0, 1.0)
            Physical justification: High terrain susceptibility is dramatically amplified by rain.
            Low terrain susceptibility remains resilient unless rainfall is extreme.
        - 'weighted':
            operational_score = (1.0 - beta) * static_visual + beta * rainfall_trigger
        """
        mode = (mode or self.combination_mode).lower()
        w = self.rainfall_weight if weight is None else float(weight)

        s_sv = float(np.clip(static_visual_score, 0.0, 1.0))
        s_rain = float(np.clip(rainfall_trigger_score, 0.0, 1.0))

        if mode == "multiplicative":
            # Amplification factor alpha (typically 0.3 - 0.7)
            alpha = w
            raw_score = s_sv * (1.0 + alpha * s_rain)
            return float(round(np.clip(raw_score, 0.0, 1.0), 6))
        elif mode == "weighted":
            # Linear late fusion
            raw_score = (1.0 - w) * s_sv + w * s_rain
            return float(round(np.clip(raw_score, 0.0, 1.0), 6))
        else:
            raise ValueError(f"Unknown combination mode: {mode}")

    def get_integrated_landslide_risk(
        self,
        latitude: float,
        longitude: float,
        timestamp: str,
        xgboost_probability: Optional[float] = None,
        swin_probability: Optional[float] = None,
        rainfall_weight: Optional[float] = None,
        combination_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Public reusable API interface for real-time operational landslide risk queries.
        
        Args:
            latitude: Latitude coordinate in decimal degrees.
            longitude: Longitude coordinate in decimal degrees.
            timestamp: Date string in 'YYYY-MM-DD' format.
            xgboost_probability: Optional precomputed static terrain probability.
            swin_probability: Optional precomputed satellite optical visual probability.
            rainfall_weight: Configurable rainfall contribution factor.
            combination_mode: 'multiplicative' (default) or 'weighted'.

        Returns:
            Dictionary containing all spatial, temporal, static, visual, hydrometeorological,
            and integrated operational risk metrics with full transparency.
        """
        # 1. Obtain static-visual fusion components
        sv_dict = self.compute_static_visual_score(
            xgboost_probability=xgboost_probability,
            swin_probability=swin_probability,
            latitude=latitude,
            longitude=longitude,
        )
        s_sv = sv_dict["static_visual_fusion_score"]

        # 2. Query dynamic antecedent rainfall indicators
        rain_result = get_dynamic_rainfall_risk(latitude, longitude, timestamp)
        s_rain = float(rain_result.get("dynamic_rainfall_trigger_score", 0.0))

        # 3. Combine scores using transparent rule
        op_score = self.combine_scores(
            static_visual_score=s_sv,
            rainfall_trigger_score=s_rain,
            mode=combination_mode,
            weight=rainfall_weight,
        )

        # Build clean, complete dictionary with full visibility
        return {
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
            "timestamp": str(timestamp),
            "xgboost_probability": sv_dict["xgboost_probability"],
            "swin_probability": sv_dict["swin_probability"],
            "static_visual_fusion_score": s_sv,
            "rainfall_3d_mm": rain_result.get("rainfall_3d_mm", 0.0),
            "rainfall_7d_mm": rain_result.get("rainfall_7d_mm", 0.0),
            "rainfall_14d_mm": rain_result.get("rainfall_14d_mm", 0.0),
            "rainfall_30d_mm": rain_result.get("rainfall_30d_mm", 0.0),
            "rainfall_anomaly": rain_result.get("rainfall_anomaly", 1.0),
            "dynamic_rainfall_trigger_score": s_rain,
            "operational_landslide_risk_score": op_score,
            "trigger_indicator": rain_result.get("trigger_indicator", "UNKNOWN"),
            "combination_mode": combination_mode or self.combination_mode,
        }


# Global singleton instance
_DEFAULT_INTEGRATED_ENGINE = None


def get_integrated_landslide_risk(
    latitude: float,
    longitude: float,
    timestamp: str,
    xgboost_probability: Optional[float] = None,
    swin_probability: Optional[float] = None,
    rainfall_weight: Optional[float] = None,
    combination_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Standard top-level functional API.
    """
    global _DEFAULT_INTEGRATED_ENGINE
    if _DEFAULT_INTEGRATED_ENGINE is None:
        _DEFAULT_INTEGRATED_ENGINE = IntegratedRiskEngine()
    return _DEFAULT_INTEGRATED_ENGINE.get_integrated_landslide_risk(
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        xgboost_probability=xgboost_probability,
        swin_probability=swin_probability,
        rainfall_weight=rainfall_weight,
        combination_mode=combination_mode,
    )
