"""
Terrain Feature Extraction and XGBoost Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

import logging
from typing import Dict, Tuple
import numpy as np
import pandas as pd

from ml.inference.config import settings
from ml.inference.model_loader import container

logger = logging.getLogger("ml.inference.feature_service")


class FeatureService:
    """Extracts terrain features and computes XGBoost susceptibility probability."""

    def __init__(self):
        pass

    def extract_features_and_predict(self, latitude: float, longitude: float) -> Tuple[float, Dict[str, float]]:
        """
        Extracts static terrain/geo-environmental features and runs XGBoost inference.

        Args:
            latitude: Target latitude in decimal degrees.
            longitude: Target longitude in decimal degrees.

        Returns:
            Tuple of (xgboost_probability, raw_features_dict).
        """
        # 1. Geographic Boundary Validation
        if not (settings.MIN_LAT <= latitude <= settings.MAX_LAT and settings.MIN_LON <= longitude <= settings.MAX_LON):
            raise ValueError(
                f"Coordinates ({latitude:.4f}, {longitude:.4f}) are outside the Uttarakhand "
                f"operational envelope [{settings.MIN_LAT}-{settings.MAX_LAT}, {settings.MIN_LON}-{settings.MAX_LON}]."
            )

        # 2. Query Nearest Training Sample
        nearest_row, dist_deg = container.query_nearest_training_features(latitude, longitude)
        if nearest_row is None:
            raise ValueError(
                f"Requested location ({latitude:.4f}, {longitude:.4f}) is outside reliable terrain feature coverage "
                f"(nearest observation is {dist_deg * 111.0:.1f} km away, threshold is {settings.MAX_NEAREST_NEIGHBOR_DISTANCE_DEG * 111.0:.1f} km)."
            )

        # 3. Assemble Raw Input Row Matching Preprocessing Pipeline Schema
        aspect_deg = float(nearest_row.get("aspect_degrees", 0.0))
        aspect_rad = np.radians(aspect_deg)
        aspect_sin = float(np.sin(aspect_rad))
        aspect_cos = float(np.cos(aspect_rad))

        raw_features = {
            "elevation_m": float(nearest_row["elevation_m"]),
            "slope_degrees": float(nearest_row["slope_degrees"]),
            "profile_curvature": float(nearest_row["profile_curvature"]),
            "plan_curvature": float(nearest_row["plan_curvature"]),
            "twi": float(nearest_row["twi"]),
            "ndvi": float(nearest_row["ndvi"]),
            "mean_annual_precipitation_mm": float(nearest_row["mean_annual_precipitation_mm"]),
            "aspect_sin": aspect_sin,
            "aspect_cos": aspect_cos,
            "lulc_class": float(nearest_row["lulc_class"]),
        }

        # 4. Transform via Preprocessing Pipeline
        input_df = pd.DataFrame([raw_features])
        X_trans = container.preprocessing_pipeline.transform(input_df)

        # 5. Predict Posterior Probability using Frozen Tuned XGBoost
        prob = float(container.xgb_model.predict_proba(X_trans)[0, 1])
        prob = float(np.clip(prob, 0.0, 1.0))

        return prob, raw_features


feature_service = FeatureService()
