"""
Generates branch output files, schema specifications, and prediction distributions
for Step 40: Multimodal Fusion Readiness & Output Alignment Audit.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

FUSION_DIR = Path("ml/reports/fusion")
FUSION_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load XGBoost Model and Split Data
xgb_model = joblib.load("ml/models/final/tuned_xgboost.joblib")
X_test = pd.read_csv("ml/data/processed/splits/X_test.csv")
y_test = pd.read_csv("ml/data/processed/splits/y_test.csv")
test_meta = pd.read_csv("ml/data/processed/splits/test_metadata.csv")

# Generate XGBoost test predictions for fusion
xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
xgb_preds = (xgb_probs >= 0.5).astype(int)

xgb_fusion_df = pd.DataFrame({
    "sample_id": test_meta["sample_id"],
    "latitude": test_meta["latitude"],
    "longitude": test_meta["longitude"],
    "landslide": test_meta["landslide"],
    "xgboost_probability": np.round(xgb_probs, 6),
    "xgboost_prediction": xgb_preds
})
xgb_fusion_path = FUSION_DIR / "xgboost_test_predictions_for_fusion.csv"
xgb_fusion_df.to_csv(xgb_fusion_path, index=False)
print(f"Saved XGBoost test predictions for fusion to {xgb_fusion_path} ({len(xgb_fusion_df)} samples)")

# 2. Format Swin test predictions for fusion
swin_orig = pd.read_csv("ml/reports/model_evaluation/swin_test_predictions.csv")
swin_fusion_df = pd.DataFrame({
    "sample_id": swin_orig["sample_id"],
    "latitude": swin_orig["latitude"],
    "longitude": swin_orig["longitude"],
    "landslide": swin_orig["landslide"],
    "swin_probability": np.round(swin_orig["swin_probability"], 6),
    "swin_prediction": swin_orig["swin_prediction"]
})
swin_fusion_path = FUSION_DIR / "swin_test_predictions_for_fusion.csv"
swin_fusion_df.to_csv(swin_fusion_path, index=False)
print(f"Saved Swin test predictions for fusion to {swin_fusion_path} ({len(swin_fusion_df)} samples)")

# 3. Load Rainfall Trigger Engine cache data
rain_cache = pd.read_parquet("ml/data/processed/rainfall/uttarakhand_grid_rainfall_cache.parquet")
rain_scores = rain_cache["dynamic_rainfall_trigger_score"].values

# 4. Generate branch prediction distributions table
def get_stats(arr, branch_name, signal_type, brier=None):
    return {
        "branch": branch_name,
        "signal_type": signal_type,
        "count": len(arr),
        "min": round(float(np.min(arr)), 6),
        "p25": round(float(np.percentile(arr, 25)), 6),
        "median": round(float(np.median(arr)), 6),
        "mean": round(float(np.mean(arr)), 6),
        "p75": round(float(np.percentile(arr, 75)), 6),
        "max": round(float(np.max(arr)), 6),
        "std": round(float(np.std(arr)), 6),
        "brier_score_loss": round(brier, 4) if brier is not None else "N/A (uncalibrated score)"
    }

brier_xgb = float(brier_score_loss(y_test["landslide"], xgb_probs))
brier_swin = float(brier_score_loss(y_test["landslide"], swin_fusion_df["swin_probability"]))

dist_df = pd.DataFrame([
    get_stats(xgb_probs, "XGBoost Branch", "Static Terrain Susceptibility Probability", brier_xgb),
    get_stats(swin_fusion_df["swin_probability"].values, "Swin Transformer Branch", "Satellite Optical Visual Risk Probability", brier_swin),
    get_stats(rain_scores, "Dynamic Rainfall Branch", "Dynamic Hydrometeorological Trigger Score", None)
])
dist_path = FUSION_DIR / "branch_prediction_distributions.csv"
dist_df.to_csv(dist_path, index=False)
print(f"Saved branch prediction distributions to {dist_path}")

# 5. Generate Branch Output Schema Specification
schema_records = [
    {
        "branch_name": "XGBoost",
        "primary_role": "Static Terrain & Environmental Susceptibility",
        "signal_name": "xgboost_probability",
        "signal_nature": "Calibrated Posterior Probability in [0, 1]",
        "spatial_scope": "Sample Coordinate / Polygon Centroid",
        "temporal_scope": "Static Climatological Baseline (10-yr Normal)",
        "test_availability": "2,210 held-out test samples strictly aligned",
        "runtime_availability": "Immediate via trained model feature vector"
    },
    {
        "branch_name": "Swin Transformer",
        "primary_role": "Satellite Optical Surface Reflectance & Visual Risk",
        "signal_name": "swin_probability",
        "signal_nature": "Calibrated Sigmoid Probability in [0, 1]",
        "spatial_scope": "128x128 pixel patch (1.28 km x 1.28 km footprint)",
        "temporal_scope": "Annual Sentinel-2 Surface Reflectance Median Composite",
        "test_availability": "2,210 held-out test samples strictly aligned",
        "runtime_availability": "Immediate via Sentinel-2 patch extraction"
    },
    {
        "branch_name": "Dynamic Rainfall Engine",
        "primary_role": "Dynamic Meteorological Triggering Stress",
        "signal_name": "dynamic_rainfall_trigger_score",
        "signal_nature": "Continuous Multi-Component Trigger Index in [0, 1]",
        "spatial_scope": "0.05 deg CHIRPS grid / Arbitrary (lat, lon)",
        "temporal_scope": "Causal 30-day Antecedent Window (t-29 to t)",
        "test_availability": "Unavailable for historical samples (zero event timestamps in inventory)",
        "runtime_availability": "Real-time via get_dynamic_rainfall_risk API"
    }
]
schema_df = pd.DataFrame(schema_records)
schema_path = FUSION_DIR / "branch_output_schema.csv"
schema_df.to_csv(schema_path, index=False)
print(f"Saved branch output schema to {schema_path}")
