"""
Configuration settings for the ML Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path


def get_project_root() -> Path:
    """Finds the root directory containing 'ml'."""
    current = Path.cwd()
    if (current / "ml").exists():
        return current
    if (current.parent / "ml").exists():
        return current.parent
    return current


PROJECT_ROOT = get_project_root()
ML_DIR = PROJECT_ROOT / "ml"


@dataclass
class Settings:
    """Application configuration and hyperparameter settings."""

    # Server Settings
    APP_NAME: str = "Uttarakhand Landslide Multimodal ML Inference Service"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("ML_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("ML_PORT", "8000"))
    DEBUG: bool = os.getenv("ML_DEBUG", "false").lower() == "true"

    # Model Artifact Paths
    XGB_MODEL_PATH: Path = ML_DIR / "models" / "final" / "tuned_xgboost.joblib"
    PREPROCESSING_PIPELINE_PATH: Path = ML_DIR / "models" / "preprocessing" / "preprocessing_pipeline.joblib"
    FEATURE_NAMES_PATH: Path = ML_DIR / "models" / "preprocessing" / "feature_names.json"
    SWIN_MODEL_PATH: Path = ML_DIR / "models" / "swin" / "swin_transformer_best.pth"
    SWIN_CONFIG_PATH: Path = ML_DIR / "models" / "swin" / "swin_transformer_config.json"
    FUSION_MODEL_PATH: Path = ML_DIR / "models" / "final" / "static_visual_fusion_model.joblib"

    # Data Paths for Runtime Reference
    MASTER_DATASET_PATH: Path = ML_DIR / "data" / "processed" / "uttarakhand_master_ml_dataset.csv"
    TRAIN_METADATA_PATH: Path = ML_DIR / "data" / "processed" / "splits" / "train_metadata.csv"
    PATCH_MANIFEST_PATH: Path = ML_DIR / "data" / "processed" / "patches" / "manifest.csv"
    PATCHES_DIR: Path = ML_DIR / "data" / "processed" / "patches"
    DEM_RASTER_PATH: Path = ML_DIR / "data" / "processed" / "dem" / "uttarakhand_dem_wgs84_30m.tif"
    RAINFALL_CACHE_PATH: Path = ML_DIR / "data" / "processed" / "rainfall" / "uttarakhand_grid_rainfall_cache.parquet"

    # Uttarakhand Operational Geospatial Envelope (WGS84 degrees)
    MIN_LAT: float = 28.50
    MAX_LAT: float = 31.60
    MIN_LON: float = 77.40
    MAX_LON: float = 81.30

    # Maximum allowed distance to a valid training observation (degrees) ~16.5 km
    MAX_NEAREST_NEIGHBOR_DISTANCE_DEG: float = 0.15

    # Frozen Static-Visual Fusion Weights (Step 41)
    FROZEN_W_XGB: float = 0.38
    FROZEN_W_SWIN: float = 0.62

    # Default Dynamic Rainfall Runtime Parameters
    DEFAULT_RAINFALL_WEIGHT: float = 0.50
    DEFAULT_COMBINATION_MODE: str = "multiplicative"

    # Operational Risk Level Thresholds (Decision-support categories)
    # Aligned with Backend RiskLevel enum: LOW, MEDIUM, HIGH, CRITICAL
    THRESHOLD_LOW: float = 0.35
    THRESHOLD_MEDIUM: float = 0.60
    THRESHOLD_HIGH: float = 0.80


settings = Settings()
