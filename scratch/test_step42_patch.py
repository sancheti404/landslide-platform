"""
End-to-End Verification of Step 42 Patch: Geographic Envelope Validation.
Uttarakhand Landslide Intelligence Platform.
"""

import json
import urllib.request
import urllib.error
import time

SPRING_BOOT_BASE = "http://localhost:8080"
FASTAPI_BASE = "http://localhost:8000"


def make_request(url: str, method: str = "GET", data: dict = None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body, timeout=15) as resp:
            status = resp.status
            content = json.loads(resp.read().decode("utf-8"))
            return status, content
    except urllib.error.HTTPError as e:
        content = json.loads(e.read().decode("utf-8"))
        return e.code, content
    except Exception as e:
        return 500, {"error": str(e)}


def test_health():
    print("\n--- 1. Health Endpoints ---")
    st_fastapi, data_fastapi = make_request(f"{FASTAPI_BASE}/health")
    print(f"FastAPI /health: status={st_fastapi}, payload={data_fastapi['status']}")
    assert st_fastapi == 200
    assert data_fastapi["status"] == "healthy"

    st_sb, data_sb = make_request(f"{SPRING_BOOT_BASE}/api/risk/ml-health")
    print(f"Spring Boot /api/risk/ml-health: status={st_sb}, payload={data_sb}")
    assert st_sb == 200
    assert data_sb["status"] == "healthy"
    print(">>> Health checks PASSED")


def test_valid_interior_point():
    print("\n--- 2. Valid Interior Coordinate (Kedarnath: 30.529505, 79.085957) ---")
    payload = {
        "latitude": 30.529505,
        "longitude": 79.085957,
        "timestamp": "2023-07-15"
    }
    t0 = time.time()
    st, resp = make_request(f"{SPRING_BOOT_BASE}/api/risk/assess", method="POST", data=payload)
    elapsed = (time.time() - t0) * 1000.0
    print(f"Spring Boot status={st} in {elapsed:.1f} ms")
    assert st == 200
    print(f"  Operational Score : {resp['operational_landslide_risk_score']} [{resp['risk_level']}]")
    print(f"  XGBoost Prob      : {resp['xgboost_probability']}")
    print(f"  Swin Prob         : {resp['swin_probability']}")
    print(f"  Static-Visual     : {resp['static_visual_fusion_score']}")
    print(f"  Rainfall Trigger  : {resp['dynamic_rainfall_trigger_score']} [{resp['trigger_indicator']}]")
    print(f"  PostGIS Zone      : {resp.get('intersecting_risk_zone_name')} [{resp.get('intersecting_risk_zone_level')}]")

    # Verify frozen fusion weights
    expected_fusion = round(0.38 * resp['xgboost_probability'] + 0.62 * resp['swin_probability'], 4)
    actual_fusion = round(resp['static_visual_fusion_score'], 4)
    assert abs(expected_fusion - actual_fusion) < 1e-3, f"Fusion weight mismatch: {expected_fusion} vs {actual_fusion}"
    print(">>> Valid interior coordinate evaluation PASSED")

    # Also test an inside-zone coordinate: Dehradun High Risk Slopes (30.42, 78.42)
    st_dehradun, resp_dehradun = make_request(f"{SPRING_BOOT_BASE}/api/risk/assess", method="POST", data={
        "latitude": 30.42, "longitude": 78.42, "timestamp": "2023-07-15"
    })
    assert st_dehradun == 200
    print(f"  Dehradun Matched PostGIS Zone: {resp_dehradun.get('intersecting_risk_zone_name')} [{resp_dehradun.get('intersecting_risk_zone_level')}]")
    assert resp_dehradun.get('intersecting_risk_zone_name') == "Dehradun High Risk Slopes"
    print(">>> PostGIS intersecting zone spatial query PASSED")


def test_discovered_bug_coordinate():
    print("\n--- 3. Discovered Bug Coordinate (29.580286, 82.808874 - Invalid Lon > 81.30) ---")
    payload = {
        "latitude": 29.580286,
        "longitude": 82.808874,
        "timestamp": "2023-07-15"
    }

    # Test via Spring Boot
    st_sb, resp_sb = make_request(f"{SPRING_BOOT_BASE}/api/risk/assess", method="POST", data=payload)
    print(f"Spring Boot Response: HTTP {st_sb} -> {resp_sb}")
    assert st_sb == 400
    err_str = json.dumps(resp_sb).lower()
    assert "81.30" in err_str or "unsupported_location" in err_str or "envelope" in err_str

    # Test via FastAPI directly
    st_fastapi, resp_fastapi = make_request(f"{FASTAPI_BASE}/risk/assess", method="POST", data=payload)
    print(f"FastAPI Response: HTTP {st_fastapi} -> {resp_fastapi}")
    assert st_fastapi == 400
    assert resp_fastapi.get("error_code") == "UNSUPPORTED_LOCATION"
    assert "outside" in resp_fastapi.get("message", "").lower()

    print(">>> Discovered bug coordinate correctly REJECTED by both layers with HTTP 400")


def test_boundary_envelope_matrix():
    print("\n--- 4. Boundary Envelope Matrix (Tests C through J) ---")
    test_cases = [
        ("Test C: Lon lower boundary 77.40", 30.0, 77.40, True),
        ("Test D: Lon upper boundary 81.30", 30.0, 81.30, True),
        ("Test E: Lon outside upper 81.300001", 30.0, 81.300001, False),
        ("Test F: Lat lower boundary 28.50", 28.50, 79.0, True),
        ("Test G: Lat upper boundary 31.60", 31.60, 79.0, True),
        ("Test H: Lat outside upper 31.600001", 31.600001, 79.0, False),
        ("Test I: Far outside (25.0, 90.0)", 25.0, 90.0, False),
    ]

    for label, lat, lon, envelope_valid in test_cases:
        st, resp = make_request(f"{SPRING_BOOT_BASE}/api/risk/assess", method="POST", data={
            "latitude": lat, "longitude": lon, "timestamp": "2023-07-15"
        })
        if not envelope_valid:
            assert st == 400, f"Expected 400 for {label}, got {st}"
            print(f"  [PASS] {label}: Rejected with HTTP {st}")
        else:
            # Envelope is valid; it may succeed OR reject with runtime coverage distance
            if st == 400:
                assert "coverage" in json.dumps(resp).lower() or "terrain" in json.dumps(resp).lower()
                print(f"  [PASS] {label}: Accepted by envelope (rejected by runtime nearest-neighbor distance protection)")
            else:
                assert st == 200
                print(f"  [PASS] {label}: Accepted and evaluated successfully")

    # Test J: Valid envelope coordinate with insufficient runtime training coverage
    # e.g. (28.51, 77.41)
    st_j, resp_j = make_request(f"{FASTAPI_BASE}/risk/assess", method="POST", data={
        "latitude": 28.51, "longitude": 77.41, "timestamp": "2023-07-15"
    })
    assert st_j == 400
    assert resp_j.get("error_code") == "UNSUPPORTED_LOCATION"
    assert "coverage" in resp_j.get("message", "").lower()
    print(f"  [PASS] Test J: Valid envelope coordinate outside training data coverage rejected with UNSUPPORTED_LOCATION")


if __name__ == "__main__":
    test_health()
    test_valid_interior_point()
    test_discovered_bug_coordinate()
    test_boundary_envelope_matrix()
    print("\n========================================================")
    print("ALL STEP 42 PATCH INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("========================================================")
