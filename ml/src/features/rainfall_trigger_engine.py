"""
Dynamic Rainfall Triggering Engine for Uttarakhand Landslide Intelligence Platform.

Calculates antecedent rainfall indicators and continuous hydrometeorological trigger scores
from CHIRPS Daily precipitation (UCSB-CHG/CHIRPS/DAILY).

IMPORTANT METHODOLOGICAL PRINCIPLES:
1. No Machine-Learning Claims:
   This is an empirical hydrometeorological stress engine, NOT a supervised ML classifier.
   Outputs are continuous trigger scores (0.0 to 1.0), NOT calibrated probabilities.
2. Anti-Leakage Guarantee:
   Calculates antecedent statistics strictly using observations available up to time t (t-30 to t).
   Never accesses rainfall occurring after the prediction timestamp.
3. Transparent Multi-Component Formulations:
   Incorporates short-term burst intensity (3d, 1d max), medium-term accumulation (7d),
   prolonged antecedent saturation (14d, 30d), and climatological anomalies.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
import math
from pathlib import Path
import threading
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

# Physical / Meteorological Reference Thresholds (Himalayan / IMD benchmarks):
# - IMD Heavy Rainfall Threshold: 64.5 - 115.5 mm/day
# - IMD Very Heavy Rainfall: > 115.5 mm/day
# - Himalayan 3-day trigger threshold (Caine 1980 / Guzzetti et al. 2007 empirical adaptation): ~150 mm
# - Himalayan 7-day cumulative saturation threshold: ~250 mm
# - Himalayan 30-day cumulative monsoon saturation threshold: ~500 mm
THRESH_1D_MAX_MM = 75.0      # 75 mm in 24h indicates severe acute slope destabilization
THRESH_3D_ACCUM_MM = 150.0   # 150 mm in 3d triggers pore-water pressure spikes in debris
THRESH_7D_ACCUM_MM = 250.0   # 250 mm in 7d leads to progressive slope saturation
THRESH_30D_ACCUM_MM = 500.0  # 500 mm in 30d reflects deep-seated hydrological recharge
BASELINE_MONSOON_DAILY_MM = 13.5  # ~405 mm/month representative Uttarakhand monsoon mean


def compute_dynamic_features_from_series(
    daily_precip_series: List[float],
    historical_expected_30d: float = 405.0
) -> Dict[str, Union[float, str]]:
    """
    Computes all required dynamic antecedent rainfall features from a 30-day daily precipitation array.
    
    Args:
        daily_precip_series: Ordered list of 30 daily rainfall values in mm, from day t-29 to day t.
        historical_expected_30d: Climatological expected 30-day total in mm for that location & season.
        
    Returns:
        Dictionary containing all dynamic features, trigger indicator, and continuous trigger score.
    """
    arr = np.array(daily_precip_series, dtype=float)
    if len(arr) < 30:
        # Pad with leading zeros if fewer than 30 days available
        pad_width = 30 - len(arr)
        arr = np.pad(arr, (pad_width, 0), mode='constant', constant_values=0.0)
    elif len(arr) > 30:
        arr = arr[-30:]

    # Clean negative or NaN values
    arr = np.nan_to_num(arr, nan=0.0)
    arr = np.maximum(arr, 0.0)

    # Accumulation windows ending at day t (the last element)
    r_3d = float(np.sum(arr[-3:]))
    r_7d = float(np.sum(arr[-7:]))
    r_14d = float(np.sum(arr[-14:]))
    r_30d = float(np.sum(arr))

    # Rolling means
    mean_3d = float(np.mean(arr[-3:]))
    mean_7d = float(np.mean(arr[-7:]))
    mean_14d = float(np.mean(arr[-14:]))
    mean_30d = float(np.mean(arr))

    # Peak intensity and cumulative
    max_daily = float(np.max(arr))
    cumulative = r_30d

    # Anomaly calculation: observed 30-day rainfall / historical expected
    expected = max(historical_expected_30d, 10.0)
    anomaly = round(float((r_30d + 1.0) / (expected + 1.0)), 3)

    # Transparent normalized sub-scores in [0.0, 1.0]
    s_1d = min(1.0, max_daily / THRESH_1D_MAX_MM)
    s_3d = min(1.0, r_3d / THRESH_3D_ACCUM_MM)
    s_7d = min(1.0, r_7d / THRESH_7D_ACCUM_MM)
    s_30d = min(1.0, r_30d / THRESH_30D_ACCUM_MM)
    s_anom = min(1.0, max(0.0, (anomaly - 0.5) / 2.0))

    # Weighted composite trigger score (0.0 to 1.0):
    # - Short-term acute burst: 35%
    # - Extreme single-day peak: 25%
    # - Medium-term cumulative: 20%
    # - Long-term antecedent saturation: 10%
    # - Climatological anomaly: 10%
    trigger_score = round(
        0.35 * s_3d + 0.25 * s_1d + 0.20 * s_7d + 0.10 * s_30d + 0.10 * s_anom,
        4
    )

    # Categorical trigger indicator
    if trigger_score < 0.20:
        indicator = "LOW_STRESS"
    elif trigger_score < 0.45:
        indicator = "MODERATE_STRESS"
    elif trigger_score < 0.70:
        indicator = "ELEVATED_TRIGGER"
    else:
        indicator = "SEVERE_TRIGGER"

    return {
        "rainfall_3d_mm": round(r_3d, 2),
        "rainfall_7d_mm": round(r_7d, 2),
        "rainfall_14d_mm": round(r_14d, 2),
        "rainfall_30d_mm": round(r_30d, 2),
        "rolling_3d_mean": round(mean_3d, 2),
        "rolling_7d_mean": round(mean_7d, 2),
        "rolling_14d_mean": round(mean_14d, 2),
        "rolling_30d_mean": round(mean_30d, 2),
        "maximum_daily_rainfall": round(max_daily, 2),
        "rainfall_anomaly": anomaly,
        "cumulative_rainfall": round(cumulative, 2),
        "trigger_indicator": indicator,
        "dynamic_rainfall_risk": trigger_score,  # Alias for requirement compatibility
        "dynamic_rainfall_trigger_score": trigger_score
    }


class DynamicRainfallEngine:
    """
    Production-ready Dynamic Rainfall Triggering Engine.
    Supports on-demand Earth Engine time-series queries and fast spatial grid lookups.
    """

    def __init__(self, cache_dir: Optional[str] = "ml/data/processed/rainfall", ee_project: str = "landslide-platform-508308"):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.ee_project = ee_project
        self._ee_initialized = False
        self._grid_cache = None
        self._memory_cache: OrderedDict = OrderedDict()
        self._series_cache: OrderedDict = OrderedDict()
        self._cache_lock = threading.Lock()
        self._max_cache_size = 4096

        if self.cache_dir and (self.cache_dir / "uttarakhand_grid_rainfall_cache.parquet").exists():
            try:
                self._grid_cache = pd.read_parquet(self.cache_dir / "uttarakhand_grid_rainfall_cache.parquet")
            except Exception:
                self._grid_cache = None

    def _ensure_ee(self):
        if not self._ee_initialized:
            import ee
            try:
                ee.Initialize(project=self.ee_project)
                self._ee_initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Earth Engine: {e}")

    def query_point_chirps_series(self, latitude: float, longitude: float, end_date_str: str) -> List[float]:
        """
        Queries exactly 30 antecedent daily CHIRPS rainfall observations ending at end_date_str.
        Thread-safe caching ensures repeated queries for identical coordinate and date avoid network roundtrips.
        """
        series_key = (round(float(latitude), 4), round(float(longitude), 4), end_date_str)
        with self._cache_lock:
            if series_key in self._series_cache:
                self._series_cache.move_to_end(series_key)
                return list(self._series_cache[series_key])

        self._ensure_ee()
        import ee

        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=29)  # 30 days total inclusive
        start_date_str = start_dt.strftime("%Y-%m-%d")
        next_day_str = (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")

        pt = ee.Geometry.Point([longitude, latitude])
        col = (
            ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterDate(start_date_str, next_day_str)
            .select("precipitation")
        )

        def extract_val(img):
            d = img.date().format("YYYY-MM-dd")
            val = img.reduceRegion(ee.Reducer.first(), pt, 5566).get("precipitation")
            return ee.Feature(None, {"date": d, "precipitation": val})

        fc = col.map(extract_val).getInfo()
        records = [f["properties"] for f in fc["features"]]

        # Sort by date
        records = sorted(records, key=lambda x: x.get("date", ""))
        values = [float(r["precipitation"]) if r.get("precipitation") is not None else 0.0 for r in records]

        # Ensure length 30
        if len(values) < 30:
            values = [0.0] * (30 - len(values)) + values
        elif len(values) > 30:
            values = values[-30:]

        with self._cache_lock:
            if len(self._series_cache) >= self._max_cache_size:
                self._series_cache.popitem(last=False)
            self._series_cache[series_key] = list(values)

        return values

    def get_dynamic_rainfall_risk(
        self,
        latitude: float,
        longitude: float,
        timestamp: str,
        sample_id: Optional[str] = None
    ) -> Dict[str, Union[float, str]]:
        """
        Public reusable API-style interface.
        Returns the latest antecedent rainfall indicators and dynamic trigger score.
        
        Args:
            latitude: Latitude coordinate in decimal degrees.
            longitude: Longitude coordinate in decimal degrees.
            timestamp: Date string in 'YYYY-MM-DD' format.
            sample_id: Optional sample identifier for fusion alignment.
        """
        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid coordinates: ({latitude}, {longitude})")

        # Extract date from timestamp
        date_str = timestamp.split("T")[0].split(" ")[0]

        # Thread-safe in-memory cache lookup
        cache_key = (round(float(latitude), 4), round(float(longitude), 4), date_str)
        with self._cache_lock:
            if cache_key in self._memory_cache:
                self._memory_cache.move_to_end(cache_key)
                cached = self._memory_cache[cache_key].copy()
                if sample_id is not None:
                    cached["sample_id"] = sample_id
                return cached

        # Fetch daily precipitation series
        daily_series = self.query_point_chirps_series(latitude, longitude, date_str)

        # Compute dynamic features
        result = compute_dynamic_features_from_series(daily_series)

        # Attach spatial, temporal, and fusion metadata
        output = {
            "sample_id": sample_id,
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
            "timestamp": date_str,
            "xgboost_probability": None,
            "swin_probability": None,
            **result
        }

        # Store in LRU cache
        with self._cache_lock:
            if len(self._memory_cache) >= self._max_cache_size:
                self._memory_cache.popitem(last=False)
            self._memory_cache[cache_key] = output.copy()

        return output


# Global default engine instance
_DEFAULT_ENGINE = None

def get_dynamic_rainfall_risk(
    latitude: float,
    longitude: float,
    timestamp: str,
    sample_id: Optional[str] = None
) -> Dict[str, Union[float, str]]:
    """
    Standard standalone functional API matching Requirement 7.
    """
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = DynamicRainfallEngine()
    return _DEFAULT_ENGINE.get_dynamic_rainfall_risk(latitude, longitude, timestamp, sample_id)
