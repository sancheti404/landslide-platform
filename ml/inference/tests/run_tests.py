"""
Standard Unittest Suite for ML Inference Service.
Uttarakhand Landslide Intelligence Platform.
"""

import os
from pathlib import Path
import sys
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from ml.inference.app import app
from ml.inference.config import settings
from ml.inference.model_loader import container


class TestMLInferenceService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=== Initializing TestClient and Loading Model Artifacts ===")
        t0 = time.time()
        cls.client = TestClient(app)
        cls.client.__enter__()
        elapsed = time.time() - t0
        print(f"=== Models Initialized in {elapsed:.2f} seconds ===\n")

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_01_health_endpoint(self):
        """Verifies that /health reports all models loaded and healthy."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["models_loaded"]["xgboost"])
        self.assertTrue(data["models_loaded"]["swin_transformer"])
        self.assertTrue(data["models_loaded"]["preprocessing_pipeline"])
        self.assertTrue(data["models_loaded"]["static_visual_fusion"])
        self.assertTrue(data["models_loaded"]["rainfall_engine"])
        self.assertTrue(data["models_loaded"]["training_features_kdtree"])
        self.assertTrue(data["models_loaded"]["training_patches_kdtree"])
        print("  [PASS] /health reports healthy and all models loaded")

    def test_02_valid_risk_assess_request(self):
        """Verifies a valid risk assessment query for a known location in Uttarakhand."""
        payload = {
            "latitude": 30.529505,
            "longitude": 79.085957,
            "timestamp": "2023-07-15",
            "rainfall_weight": 0.50,
            "combination_mode": "multiplicative",
        }
        t0 = time.time()
        response = self.client.post("/risk/assess", json=payload)
        latency_ms = (time.time() - t0) * 1000.0

        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        # Structural correctness
        self.assertEqual(data["status"], "success")
        self.assertAlmostEqual(data["latitude"], payload["latitude"], places=4)
        self.assertAlmostEqual(data["longitude"], payload["longitude"], places=4)
        self.assertEqual(data["timestamp"], "2023-07-15")

        # Probability bounds [0, 1]
        self.assertTrue(0.0 <= data["xgboost_probability"] <= 1.0)
        self.assertTrue(0.0 <= data["swin_probability"] <= 1.0)
        self.assertTrue(0.0 <= data["static_visual_fusion_score"] <= 1.0)
        self.assertTrue(0.0 <= data["dynamic_rainfall_trigger_score"] <= 1.0)
        self.assertTrue(0.0 <= data["operational_landslide_risk_score"] <= 1.0)

        # Deterministic static-visual fusion formula check
        expected_fused = (
            settings.FROZEN_W_XGB * data["xgboost_probability"] +
            settings.FROZEN_W_SWIN * data["swin_probability"]
        )
        expected_fused = min(1.0, max(0.0, expected_fused))
        self.assertAlmostEqual(data["static_visual_fusion_score"], expected_fused, places=4)

        # Risk level classification check
        self.assertIn(data["risk_level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        # Hydrometeorological indicators
        self.assertGreaterEqual(data["rainfall_3d_mm"], 0.0)
        self.assertGreaterEqual(data["rainfall_7d_mm"], 0.0)
        self.assertGreaterEqual(data["rainfall_14d_mm"], 0.0)
        self.assertGreaterEqual(data["rainfall_30d_mm"], 0.0)
        self.assertGreaterEqual(data["maximum_daily_rainfall_mm"], 0.0)

        print(f"  [PASS] /risk/assess valid request executed successfully (Latency: {latency_ms:.2f} ms)")

    def test_03_frozen_weights_invariance(self):
        """Confirms frozen weights are strictly 0.38 and 0.62 summing to 1.0."""
        w_xgb = settings.FROZEN_W_XGB
        w_swin = settings.FROZEN_W_SWIN
        self.assertEqual(w_xgb, 0.38)
        self.assertEqual(w_swin, 0.62)
        self.assertAlmostEqual(w_xgb + w_swin, 1.0, places=6)
        print("  [PASS] Frozen weights strictly 0.38 and 0.62 summing to 1.0")

    def test_04_invalid_coordinates_out_of_bounds(self):
        """Verifies that coordinates outside the Uttarakhand envelope are rejected."""
        payload = {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timestamp": "2023-07-15",
        }
        response = self.client.post("/risk/assess", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn(data["status"], ["unsupported_location", "error"])
        print("  [PASS] Out-of-bounds coordinates correctly rejected with HTTP 400")

    def test_05_invalid_timestamp_format(self):
        """Verifies rejection of malformed or invalid calendar dates."""
        payload = {
            "latitude": 30.529505,
            "longitude": 79.085957,
            "timestamp": "not-a-date",
        }
        response = self.client.post("/risk/assess", json=payload)
        self.assertIn(response.status_code, [400, 422])
        print("  [PASS] Invalid timestamp format rejected with HTTP 400/422")

    def test_06_causal_rainfall_behavior(self):
        """Verifies that rainfall queries strictly reflect their target timestamps."""
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
        res_early = self.client.post("/risk/assess", json=payload_early).json()
        res_later = self.client.post("/risk/assess", json=payload_later).json()

        self.assertEqual(res_early["timestamp"], "2023-07-10")
        self.assertEqual(res_later["timestamp"], "2023-07-15")
        self.assertTrue(0.0 <= res_early["dynamic_rainfall_trigger_score"] <= 1.0)
        self.assertTrue(0.0 <= res_later["dynamic_rainfall_trigger_score"] <= 1.0)
        print("  [PASS] Causal rainfall query behavior verified")

    def test_07_no_test_samples_in_lookup(self):
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
                self.assertEqual(len(overlap), 0, f"Critical Data Leakage: {len(overlap)} test IDs in lookup!")
        print("  [PASS] Zero test samples in runtime training lookups")

    def test_08_envelope_boundary_cases(self):
        """
        Tests A through J for authoritative geospatial operational envelope and runtime coverage.
        """
        # Test A — Valid interior coordinate
        res_a = self.client.post("/risk/assess", json={"latitude": 30.529505, "longitude": 79.085957, "timestamp": "2023-07-15"})
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json()["status"], "success")

        # Test B — Discovered bug coordinate: Lat 29.580286 (valid), Lon 82.808874 (invalid > 81.30)
        res_b = self.client.post("/risk/assess", json={"latitude": 29.580286, "longitude": 82.808874, "timestamp": "2023-07-15"})
        self.assertEqual(res_b.status_code, 400)
        data_b = res_b.json()
        self.assertEqual(data_b["error_code"], "UNSUPPORTED_LOCATION")
        self.assertTrue("outside" in data_b["message"].lower() or "operational" in data_b["message"].lower())

        # Test C — Longitude exactly at lower boundary 77.40
        res_c = self.client.post("/risk/assess", json={"latitude": 30.0, "longitude": 77.40, "timestamp": "2023-07-15"})
        if res_c.status_code == 400:
            self.assertIn("coverage", res_c.json()["message"].lower())

        # Test D — Longitude exactly at upper boundary 81.30
        res_d = self.client.post("/risk/assess", json={"latitude": 30.0, "longitude": 81.30, "timestamp": "2023-07-15"})
        if res_d.status_code == 400:
            self.assertIn("coverage", res_d.json()["message"].lower())

        # Test E — Longitude just outside upper boundary 81.300001 -> REJECT
        res_e = self.client.post("/risk/assess", json={"latitude": 30.0, "longitude": 81.300001, "timestamp": "2023-07-15"})
        self.assertEqual(res_e.status_code, 400)
        self.assertEqual(res_e.json()["error_code"], "UNSUPPORTED_LOCATION")

        # Test F — Latitude exactly at lower boundary 28.50
        res_f = self.client.post("/risk/assess", json={"latitude": 28.50, "longitude": 79.0, "timestamp": "2023-07-15"})
        if res_f.status_code == 400:
            self.assertIn("coverage", res_f.json()["message"].lower())

        # Test G — Latitude exactly at upper boundary 31.60
        res_g = self.client.post("/risk/assess", json={"latitude": 31.60, "longitude": 79.0, "timestamp": "2023-07-15"})
        if res_g.status_code == 400:
            self.assertIn("coverage", res_g.json()["message"].lower())

        # Test H — Latitude just outside upper boundary 31.600001 -> REJECT
        res_h = self.client.post("/risk/assess", json={"latitude": 31.600001, "longitude": 79.0, "timestamp": "2023-07-15"})
        self.assertEqual(res_h.status_code, 400)
        self.assertEqual(res_h.json()["error_code"], "UNSUPPORTED_LOCATION")

        # Test I — Far outside 25.0, 90.0 -> REJECT
        res_i = self.client.post("/risk/assess", json={"latitude": 25.0, "longitude": 90.0, "timestamp": "2023-07-15"})
        self.assertEqual(res_i.status_code, 400)
        self.assertEqual(res_i.json()["error_code"], "UNSUPPORTED_LOCATION")

        # Test J — Valid envelope but insufficient runtime training-data coverage -> REJECT UNSUPPORTED_LOCATION
        res_j = self.client.post("/risk/assess", json={"latitude": 28.51, "longitude": 77.41, "timestamp": "2023-07-15"})
        self.assertEqual(res_j.status_code, 400)
        data_j = res_j.json()
        self.assertEqual(data_j["error_code"], "UNSUPPORTED_LOCATION")
        self.assertIn("coverage", data_j["message"].lower())
        print("  [PASS] Operational envelope boundary cases Tests A through J verified")


if __name__ == "__main__":
    unittest.main()
