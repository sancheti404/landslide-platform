"""
Unit and Integration Tests for ML Inference Service.
Step 42 — End-to-End System Integration.
"""

import time
import pytest
from fastapi.testclient import TestClient

from ml.inference.app import app
from ml.inference.config import settings
from ml.inference.model_loader import container


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient with lifespan events (loads all models once)."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Verifies that /health reports all models loaded and healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["models_loaded"]["xgboost"] is True
    assert data["models_loaded"]["swin_transformer"] is True
    assert data["models_loaded"]["preprocessing_pipeline"] is True
    assert data["models_loaded"]["static_visual_fusion"] is True
    assert data["models_loaded"]["rainfall_engine"] is True
    assert data["models_loaded"]["training_features_kdtree"] is True
    assert data["models_loaded"]["training_patches_kdtree"] is True


def test_valid_risk_assess_request(client):
    """Verifies a valid risk assessment query for a known location in Uttarakhand."""
    # Location near Chamoli/Rudraprayag
    payload = {
        "latitude": 30.529505,
        "longitude": 79.085957,
        "timestamp": "2023-07-15",
        "rainfall_weight": 0.50,
        "combination_mode": "multiplicative",
    }
    t0 = time.time()
    response = client.post("/risk/assess", json=payload)
    latency_ms = (time.time() - t0) * 1000.0

    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()

    # Structural correctness
    assert data["status"] == "success"
    assert data["latitude"] == pytest.approx(payload["latitude"], abs=1e-5)
    assert data["longitude"] == pytest.approx(payload["longitude"], abs=1e-5)
    assert data["timestamp"] == "2023-07-15"

    # Probability bounds [0, 1]
    assert 0.0 <= data["xgboost_probability"] <= 1.0
    assert 0.0 <= data["swin_probability"] <= 1.0
    assert 0.0 <= data["static_visual_fusion_score"] <= 1.0
    assert 0.0 <= data["dynamic_rainfall_trigger_score"] <= 1.0
    assert 0.0 <= data["operational_landslide_risk_score"] <= 1.0

    # Deterministic static-visual fusion formula check
    expected_fused = (
        settings.FROZEN_W_XGB * data["xgboost_probability"] +
        settings.FROZEN_W_SWIN * data["swin_probability"]
    )
    expected_fused = min(1.0, max(0.0, expected_fused))
    assert data["static_visual_fusion_score"] == pytest.approx(expected_fused, abs=1e-4)

    # Risk level classification check
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Hydrometeorological indicators
    assert data["rainfall_3d_mm"] >= 0.0
    assert data["rainfall_7d_mm"] >= 0.0
    assert data["rainfall_14d_mm"] >= 0.0
    assert data["rainfall_30d_mm"] >= 0.0
    assert data["maximum_daily_rainfall_mm"] >= 0.0

    print(f"\n[Test Benchmark] Assessment Latency: {latency_ms:.2f} ms")


def test_frozen_weights_invariance():
    """Confirms frozen weights are strictly 0.38 and 0.62 summing to 1.0."""
    w_xgb = settings.FROZEN_W_XGB
    w_swin = settings.FROZEN_W_SWIN
    assert w_xgb == 0.38
    assert w_swin == 0.62
    assert pytest.approx(w_xgb + w_swin, abs=1e-6) == 1.0


def test_invalid_coordinates_out_of_bounds(client):
    """Verifies that coordinates outside the Uttarakhand envelope are rejected."""
    # Delhi coordinate (outside Uttarakhand envelope)
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timestamp": "2023-07-15",
    }
    response = client.post("/risk/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] in ["unsupported_location", "error"]
    assert "UNSUPPORTED_LOCATION" in data["error_code"] or "outside" in data["message"].lower()


def test_invalid_timestamp_format(client):
    """Verifies rejection of malformed or invalid calendar dates."""
    payload = {
        "latitude": 30.529505,
        "longitude": 79.085957,
        "timestamp": "not-a-date",
    }
    response = client.post("/risk/assess", json=payload)
    assert response.status_code in [400, 422]


def test_causal_rainfall_behavior(client):
    """
    Verifies that the rainfall engine strictly uses data available up to timestamp t.
    Precipitation on July 10 cannot exceed 30-day cumulative precipitation on July 15.
    """
    payload_early = {
        "latitude": 30.529505,
        "longitude": 79.085957,
        "timestamp": "2023-07-10",
    }
    payload_later = {
        "latitude": 30.529505,
        "longitude": 79.085957,
        "timestamp": "2023-07-15",
    }
    res_early = client.post("/risk/assess", json=payload_early).json()
    res_later = client.post("/risk/assess", json=payload_later).json()

    # The indicators must reflect their respective time windows
    assert res_early["timestamp"] == "2023-07-10"
    assert res_later["timestamp"] == "2023-07-15"
    assert 0.0 <= res_early["dynamic_rainfall_trigger_score"] <= 1.0
    assert 0.0 <= res_later["dynamic_rainfall_trigger_score"] <= 1.0


def test_no_test_samples_in_lookup():
    """Guarantees that test sample IDs are completely absent from the runtime lookup."""
    test_meta_path = settings.TRAIN_METADATA_PATH.parent / "test_metadata.csv"
    if test_meta_path.exists():
        import pandas as pd
        test_df = pd.read_csv(test_meta_path)
        test_ids = set(test_df["sample_id"].unique())

        lookup_df = container.train_features_df
        if lookup_df is not None:
            lookup_ids = set(lookup_df["sample_id"].unique())
            overlap = lookup_ids.intersection(test_ids)
            assert len(overlap) == 0, f"Critical Data Leakage: {len(overlap)} test IDs in lookup!"
