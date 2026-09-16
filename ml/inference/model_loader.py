"""
Singleton Model Loader and Runtime Cache for the ML Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import torch

from ml.inference.config import settings
from ml.src.features.rainfall_trigger_engine import DynamicRainfallEngine
from ml.src.models.swin_model import SwinLandslideClassifier

logger = logging.getLogger("ml.inference.model_loader")


class ModelContainer:
    """Holds loaded model artifacts and spatial reference data in memory."""

    def __init__(self):
        self.is_loaded: bool = False
        self.device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.start_time: float = time.time()

        # Models
        self.xgb_model: Any = None
        self.preprocessing_pipeline: Any = None
        self.feature_names: Dict[str, Any] = {}
        self.swin_model: Optional[SwinLandslideClassifier] = None
        self.fusion_config: Dict[str, Any] = {}
        self.rainfall_engine: Optional[DynamicRainfallEngine] = None

        # Spatial Training Lookup (Strictly Training Split - Never Test Data)
        self.train_features_df: Optional[pd.DataFrame] = None
        self.train_features_kdtree: Optional[cKDTree] = None

        self.train_patches_df: Optional[pd.DataFrame] = None
        self.train_patches_kdtree: Optional[cKDTree] = None

    def load_all(self):
        """Loads all frozen model artifacts and builds training spatial lookups."""
        logger.info("Initializing ML models on device: %s", self.device)

        # 1. XGBoost Model
        if not settings.XGB_MODEL_PATH.exists():
            raise FileNotFoundError(f"Missing XGBoost artifact: {settings.XGB_MODEL_PATH}")
        self.xgb_model = joblib.load(settings.XGB_MODEL_PATH)
        logger.info("Loaded tuned XGBoost model from %s", settings.XGB_MODEL_PATH)

        # 2. Preprocessing Pipeline & Feature Names
        if not settings.PREPROCESSING_PIPELINE_PATH.exists():
            raise FileNotFoundError(f"Missing Preprocessing artifact: {settings.PREPROCESSING_PIPELINE_PATH}")
        self.preprocessing_pipeline = joblib.load(settings.PREPROCESSING_PIPELINE_PATH)

        if not settings.FEATURE_NAMES_PATH.exists():
            raise FileNotFoundError(f"Missing Feature Names JSON: {settings.FEATURE_NAMES_PATH}")
        with open(settings.FEATURE_NAMES_PATH, "r", encoding="utf-8") as f:
            self.feature_names = json.load(f)
        logger.info("Loaded tabular preprocessing pipeline and feature names")

        # 3. Swin Transformer Model
        if not settings.SWIN_MODEL_PATH.exists():
            raise FileNotFoundError(f"Missing Swin checkpoint: {settings.SWIN_MODEL_PATH}")
        self.swin_model = SwinLandslideClassifier(pretrained=False)
        swin_weights = torch.load(settings.SWIN_MODEL_PATH, map_location=self.device)
        self.swin_model.load_state_dict(swin_weights)
        self.swin_model.to(self.device)
        self.swin_model.eval()
        logger.info("Loaded Swin Transformer model from %s", settings.SWIN_MODEL_PATH)

        # 4. Static-Visual Fusion Model
        if settings.FUSION_MODEL_PATH.exists():
            self.fusion_config = joblib.load(settings.FUSION_MODEL_PATH)
            logger.info("Loaded static-visual fusion configuration: %s", self.fusion_config.get("selected_method"))
        else:
            self.fusion_config = {
                "w_xgb": settings.FROZEN_W_XGB,
                "w_swin": settings.FROZEN_W_SWIN,
            }
            logger.warning("Fusion model artifact not found, using frozen defaults: w_xgb=%.2f, w_swin=%.2f",
                           settings.FROZEN_W_XGB, settings.FROZEN_W_SWIN)

        # 5. Dynamic Rainfall Trigger Engine
        self.rainfall_engine = DynamicRainfallEngine()
        logger.info("Loaded Dynamic Rainfall Trigger Engine")

        # 6. Spatial Training Lookups (Strictly Training Samples Only)
        self._build_training_lookups()

        self.is_loaded = True
        logger.info("All model artifacts and spatial reference structures successfully loaded.")

    def _build_training_lookups(self):
        """Constructs spatial KD-trees strictly using training data to prevent test leakage."""
        logger.info("Building spatial training lookup structures...")

        # A. Tabular Feature Reference (Master dataset filtered strictly to train_metadata IDs)
        if settings.MASTER_DATASET_PATH.exists() and settings.TRAIN_METADATA_PATH.exists():
            master_df = pd.read_csv(settings.MASTER_DATASET_PATH)
            train_meta = pd.read_csv(settings.TRAIN_METADATA_PATH)

            # Strict training filter
            train_ids = set(train_meta["sample_id"].unique())
            self.train_features_df = master_df[master_df["sample_id"].isin(train_ids)].reset_index(drop=True)
            logger.info("Filtered training master feature dataset: %d samples (0 test samples)", len(self.train_features_df))

            coords = np.column_stack([
                self.train_features_df["latitude"].values,
                self.train_features_df["longitude"].values
            ])
            self.train_features_kdtree = cKDTree(coords)
        else:
            logger.warning("Training master feature dataset not found at %s", settings.MASTER_DATASET_PATH)

        # B. Satellite Patch Reference (Manifest filtered strictly to train split)
        if settings.PATCH_MANIFEST_PATH.exists():
            manifest_df = pd.read_csv(settings.PATCH_MANIFEST_PATH)
            self.train_patches_df = manifest_df[manifest_df["split"] == "train"].reset_index(drop=True)
            logger.info("Filtered training patch manifest: %d samples (0 test samples)", len(self.train_patches_df))

            patch_coords = np.column_stack([
                self.train_patches_df["latitude"].values,
                self.train_patches_df["longitude"].values
            ])
            self.train_patches_kdtree = cKDTree(patch_coords)
        else:
            logger.warning("Patch manifest not found at %s", settings.PATCH_MANIFEST_PATH)

    def query_nearest_training_features(self, lat: float, lon: float) -> Tuple[Optional[pd.Series], float]:
        """
        Finds the nearest training feature vector within the spatial KD-tree.
        Returns: (feature_row, distance_degrees)
        """
        if self.train_features_kdtree is None or self.train_features_df is None:
            return None, float("inf")

        dist, idx = self.train_features_kdtree.query([lat, lon], k=1)
        if dist > settings.MAX_NEAREST_NEIGHBOR_DISTANCE_DEG:
            return None, float(dist)
        return self.train_features_df.iloc[idx], float(dist)

    def query_nearest_training_patch(self, lat: float, lon: float) -> Tuple[Optional[str], float]:
        """
        Finds the nearest training Sentinel-2 patch within the spatial KD-tree.
        Returns: (image_path, distance_degrees)
        """
        if self.train_patches_kdtree is None or self.train_patches_df is None:
            return None, float("inf")

        dist, idx = self.train_patches_kdtree.query([lat, lon], k=1)
        if dist > settings.MAX_NEAREST_NEIGHBOR_DISTANCE_DEG:
            return None, float(dist)

        row = self.train_patches_df.iloc[idx]
        img_path_str = row["image_path"]
        img_path = Path(img_path_str)
        if not img_path.is_absolute():
            img_path = settings.PATCHES_DIR / f"{row['sample_id']}.png"

        if not img_path.exists():
            return None, float(dist)
        return str(img_path), float(dist)

    def get_health_status(self) -> Dict[str, Any]:
        """Returns health information for /health endpoint."""
        return {
            "status": "healthy" if self.is_loaded else "initializing",
            "models_loaded": {
                "xgboost": self.xgb_model is not None,
                "preprocessing_pipeline": self.preprocessing_pipeline is not None,
                "swin_transformer": self.swin_model is not None,
                "static_visual_fusion": bool(self.fusion_config),
                "rainfall_engine": self.rainfall_engine is not None,
                "training_features_kdtree": self.train_features_kdtree is not None,
                "training_patches_kdtree": self.train_patches_kdtree is not None,
            },
            "device": str(self.device),
            "uptime_seconds": round(time.time() - self.start_time, 2),
        }


# Global container instance
container = ModelContainer()
