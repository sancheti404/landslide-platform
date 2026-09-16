import time
import statistics
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.feature_service import feature_service
from ml.inference.swin_service import swin_service
from ml.inference.model_loader import container
from ml.src.features.rainfall_trigger_engine import compute_dynamic_features_from_series

container.load_all()

lat = 30.529505
lon = 79.085957
date_str = "2023-07-15"

xgb_times = []
swin_times = []
rain_times = []

print("=== WARMING UP COMPONENTS ===")
# 1 warmup
p_xgb, _ = feature_service.extract_features_and_predict(lat, lon)
p_swin, _ = swin_service.predict_visual_risk(lat, lon)
rain_res = container.rainfall_engine.get_dynamic_rainfall_risk(lat, lon, date_str)

print("=== MEASURING 5 WARM RUNS ===")
for i in range(5):
    # XGBoost + feature extraction
    t0 = time.perf_counter()
    p_xgb, _ = feature_service.extract_features_and_predict(lat, lon)
    t_xgb = (time.perf_counter() - t0) * 1000.0
    xgb_times.append(t_xgb)

    # Swin Transformer
    t0 = time.perf_counter()
    p_swin, _ = swin_service.predict_visual_risk(lat, lon)
    t_swin = (time.perf_counter() - t0) * 1000.0
    swin_times.append(t_swin)

    # Rainfall Engine
    t0 = time.perf_counter()
    rain_res = container.rainfall_engine.get_dynamic_rainfall_risk(lat, lon, date_str)
    t_rain = (time.perf_counter() - t0) * 1000.0
    rain_times.append(t_rain)

    print(f"Run {i+1}: XGBoost={t_xgb:.2f} ms, Swin={t_swin:.2f} ms, Rainfall={t_rain:.2f} ms")

print("\n=== COMPONENT BREAKDOWN SUMMARY ===")
print(f"XGBoost  : Mean={statistics.mean(xgb_times):.2f} ms | Min={min(xgb_times):.2f} ms | Max={max(xgb_times):.2f} ms")
print(f"Swin     : Mean={statistics.mean(swin_times):.2f} ms | Min={min(swin_times):.2f} ms | Max={max(swin_times):.2f} ms")
print(f"Rainfall : Mean={statistics.mean(rain_times):.2f} ms | Min={min(rain_times):.2f} ms | Max={max(rain_times):.2f} ms")
