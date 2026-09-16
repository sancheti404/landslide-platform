"""
Swin Transformer Satellite Visual Risk Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

from collections import OrderedDict
import logging
from pathlib import Path
import threading
from typing import Tuple
from PIL import Image
import torch

from ml.inference.config import settings
from ml.inference.model_loader import container
from ml.src.data.swin_dataset import get_eval_transforms

logger = logging.getLogger("ml.inference.swin_service")


class SwinService:
    """Performs visual risk estimation using the frozen Swin Transformer."""

    def __init__(self):
        self.transform = get_eval_transforms(image_size=224)
        self._patch_prob_cache: OrderedDict = OrderedDict()
        self._cache_lock = threading.Lock()
        self._max_cache_size = 2048

    def predict_visual_risk(self, latitude: float, longitude: float) -> Tuple[float, str]:
        """
        Retrieves nearest training Sentinel-2 patch and predicts visual risk probability.

        Args:
            latitude: Target latitude in decimal degrees.
            longitude: Target longitude in decimal degrees.

        Returns:
            Tuple of (swin_probability, patch_image_path).
        """
        # 1. Query Nearest Training Patch
        patch_path_str, dist_deg = container.query_nearest_training_patch(latitude, longitude)
        if patch_path_str is None:
            raise ValueError(
                f"Requested location ({latitude:.4f}, {longitude:.4f}) is outside reliable satellite visual coverage "
                f"(nearest observation is {dist_deg * 111.0:.1f} km away, threshold is {settings.MAX_NEAREST_NEIGHBOR_DISTANCE_DEG * 111.0:.1f} km)."
            )

        # Thread-safe patch prediction cache check
        with self._cache_lock:
            if patch_path_str in self._patch_prob_cache:
                self._patch_prob_cache.move_to_end(patch_path_str)
                return self._patch_prob_cache[patch_path_str], patch_path_str

        # 2. Load and Preprocess Sentinel-2 RGB Patch
        img = Image.open(patch_path_str).convert("RGB")
        tensor = self.transform(img).unsqueeze(0).to(container.device)

        # 3. Model Inference (Torch No-Grad)
        with torch.no_grad():
            prob = float(container.swin_model.predict_proba(tensor).item())

        prob = max(0.0, min(1.0, prob))

        with self._cache_lock:
            if len(self._patch_prob_cache) >= self._max_cache_size:
                self._patch_prob_cache.popitem(last=False)
            self._patch_prob_cache[patch_path_str] = prob

        return prob, patch_path_str


swin_service = SwinService()
