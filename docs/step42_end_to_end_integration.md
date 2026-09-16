# STEP 42: END-TO-END LANDSLIDE RISK PLATFORM INTEGRATION
**Uttarakhand Landslide Intelligence Platform**
*Date: 2026-09-16 | Status: Complete & Verified | Phase: Software & Platform Integration*

---

## 1. System Architecture Overview

The platform transitions from standalone machine learning research into an enterprise-grade, microservice-based landslide intelligence system:

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           CLIENT TIER                                  │
  │   Interactive Leaflet GIS Map Web UI  (http://localhost:8080/index.html)│
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ REST: POST /api/risk/assess
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                       APPLICATION GATEWAY TIER                         │
  │   Spring Boot 4.1.1 Enterprise Backend  (Port 8080)                    │
  │   - Security, CORS, DTO Validation (Hibernate Validator)              │
  │   - PostGIS 18.6 Spatial Engine (ST_Contains, ST_Intersects)           │
  │   - RiskZone & Critical Infrastructure Proximity Context               │
  │   - Resilient RestClient with Configurable Timeouts                    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ HTTP: POST /risk/assess
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         ML INFERENCE TIER                              │
  │   Python FastAPI Dedicated Microservice  (Port 8000)                   │
  │   ├── Model Lifespan Manager (Single in-memory pre-load)               │
  │   │   ├── Tuned XGBoost (318 KB)                                       │
  │   │   ├── Preprocessing Pipeline & Feature Schema                      │
  │   │   ├── Swin-Tiny Transformer (110 MB checkpoint, CUDA/CPU)          │
  │   │   ├── Frozen Static-Visual Late Fusion (0.38 XGB + 0.62 Swin)      │
  │   │   └── Dynamic CHIRPS Rainfall Engine (30-day causal window)        │
  │   ├── Feature Extraction Service (DEM + Training KDTree)               │
  │   └── Operational Risk Engine (Decision Support Heuristic)             │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Artifacts & Immutability Guarantee

All machine learning models and fusion parameters established in Steps 36–41 are **100% frozen**:
- **XGBoost Terrain Branch**: `ml/models/final/tuned_xgboost.joblib` (unmodified).
- **Tabular Preprocessing**: `ml/models/preprocessing/preprocessing_pipeline.joblib` & `feature_names.json`.
- **Swin Vision Branch**: `ml/models/swin/swin_transformer_best.pth` & `swin_transformer_config.json` (unmodified).
- **Static-Visual Fusion**: `ml/models/final/static_visual_fusion_model.joblib` ($w_{\text{xgb}} = 0.38, w_{\text{swin}} = 0.62$).
- **Dynamic Rainfall**: `ml/src/features/rainfall_trigger_engine.py` using CHIRPS daily precipitations (causal up to timestamp $t$).
- **Strict Anti-Leakage Rule**: The runtime spatial lookup KD-trees strictly index the **8,836 training observations**. Zero held-out test points are included in runtime reference caches.

---

## 3. Mathematical Formulations

### A. Static-Visual ML Fusion (Empirical Probabilities)
$$P_{\text{static\_visual}} = 0.38 \cdot P_{\text{xgb}} + 0.62 \cdot P_{\text{swin}}$$
- Both base inputs $P_{\text{xgb}}, P_{\text{swin}} \in [0.0, 1.0]$ are calibrated posterior probabilities.
- Resulting $P_{\text{static\_visual}} \in [0.0, 1.0]$ reflects spatial susceptibility and optical surface disturbance.

### B. Dynamic Hydrometeorological Triggering (Physical Stress)
- Causal 30-day antecedent precipitation window: $t-29$ to $t$.
- Multi-component index:
  $$S_{\text{rain}} = 0.35 \cdot s_{\text{3d}} + 0.25 \cdot s_{\text{1d}} + 0.20 \cdot s_{\text{7d}} + 0.10 \cdot s_{\text{30d}} + 0.10 \cdot s_{\text{anom}}$$
- Classifies into: `LOW_STRESS`, `MODERATE_STRESS`, `ELEVATED_TRIGGER`, `SEVERE_TRIGGER`.

### C. Operational Dynamic Risk Integration
$$\text{operational\_landslide\_risk\_score} = \min\left(1.0, \; P_{\text{static\_visual}} \cdot \left(1.0 + \alpha \cdot S_{\text{rain}}\right)\right)$$
- Default amplification factor $\alpha = 0.50$ (configurable).
- Operational Risk Level Thresholds:
  - `LOW`: $[0.00, 0.35)$
  - `MEDIUM`: $[0.35, 0.60)$
  - `HIGH`: $[0.60, 0.80)$
  - `CRITICAL`: $[0.80, 1.00]$

---

## 4. API Request & Response Specifications

### `POST /api/risk/assess` (Spring Boot Gateway)
**Request Body**:
```json
{
  "latitude": 30.529505,
  "longitude": 79.085957,
  "timestamp": "2023-07-15"
}
```

**Response Body**:
```json
{
  "latitude": 30.529505,
  "longitude": 79.085957,
  "timestamp": "2023-07-15",
  "xgboost_probability": 0.919816,
  "swin_probability": 0.999899,
  "static_visual_fusion_score": 0.969468,
  "rainfall_3d_mm": 77.37,
  "rainfall_7d_mm": 242.44,
  "rainfall_14d_mm": 284.41,
  "rainfall_30d_mm": 415.58,
  "maximum_daily_rainfall_mm": 77.37,
  "rainfall_anomaly": 1.026,
  "dynamic_rainfall_trigger_score": 0.7339,
  "trigger_indicator": "SEVERE_TRIGGER",
  "operational_landslide_risk_score": 1.0,
  "risk_level": "CRITICAL",
  "model_version": "1.0.0",
  "status": "success",
  "intersecting_risk_zone_id": null,
  "intersecting_risk_zone_name": null,
  "intersecting_risk_zone_level": null,
  "nearby_hospitals_count": 0,
  "nearby_shelters_count": 0,
  "nearby_police_stations_count": 0,
  "nearby_roads_count": 0
}
```

---

## 5. Latency Profiling & Performance Telemetry

Measured on NVIDIA GeForce RTX 3050 Laptop GPU (CUDA 12.8) and Intel Core i5 Host:
- **FastAPI Startup Model Pre-loading**: **5.30 seconds** (models loaded once at boot).
- **Cold-Start Request Latency**: **818.68 ms** (initial Earth Engine handshake & CUDA kernel compilation).
- **Warm Inference Latency (via Spring Boot Gateway)**:
  - Run 1: 610.25 ms
  - Run 2: 914.29 ms
  - Run 3: 658.27 ms
  - **Average Warm Latency**: **727.60 ms**
- **Bottleneck Analysis**:
  - ~65% of latency is the CHIRPS antecedent precipitation extraction over the 30-day temporal window.
  - ~25% is Swin-Tiny vision transformer forward pass.
  - ~10% is Spring Boot JSON serialization and PostGIS point-in-polygon checks.

---

## 6. How to Run the Platform

### A. Start the Python ML Inference Service (Port 8000)
```bash
# In landslide-platform root directory
python -m uvicorn ml.inference.app:app --host 0.0.0.0 --port 8000
```
Verify readiness:
```bash
curl http://localhost:8000/health
```

### B. Start the Spring Boot Application Gateway (Port 8080)
```bash
# In landslide-platform/backend directory
./mvnw spring-boot:run
```
(On Windows: `mvnw.cmd spring-boot:run`)

### C. Access the Interactive GIS Map Interface
Open in browser:
```
http://localhost:8080/index.html
```
- Click anywhere on the Uttarakhand map to inspect risk.
- Choose presets (Kedarnath, Chamoli, Nainital, Rishikesh).
- View decomposed component signals, rainfall gauges, and PostGIS infrastructure context.

---

## 7. Strict Scientific Disclaimers

1. **Uncalibrated Dynamic Score**: The final `operational_landslide_risk_score` is a decision-support heuristic for emergency prioritization. It is **NOT** a calibrated Bayesian probability.
2. **Temporal Supervised Separation**: A Temporal Fusion Transformer (TFT) was intentionally **NOT** trained because historical inventories lack verified day-level failure timestamps.
3. **Generalization Scope**: The model is validated on the Uttarakhand Himalayan region. Spatially independent out-of-region generalization should not be claimed without external validation.
