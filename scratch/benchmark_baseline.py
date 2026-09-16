"""
Performance Baseline Measurement for Step 43.
Measures baseline latencies of current Step 42 system across all components.
"""

import json
import statistics
import time
import urllib.request

SPRING_BOOT_BASE = "http://localhost:8080"
FASTAPI_BASE = "http://localhost:8000"

TEST_COORDS = {
    "latitude": 30.529505,
    "longitude": 79.085957,
    "timestamp": "2023-07-15"
}


def time_http_request(url: str, method: str = "GET", data: dict = None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data else None
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, data=body, timeout=30) as resp:
        content = json.loads(resp.read().decode("utf-8"))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return elapsed_ms, content


def compute_stats(latencies):
    return {
        "min": min(latencies),
        "max": max(latencies),
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    }


def run_benchmarks():
    print("==================================================")
    print("STEP 43 PHASE 2: PERFORMANCE BASELINE MEASUREMENT")
    print("==================================================")

    # 1. FastAPI /health
    health_latencies = []
    for _ in range(5):
        lat, _ = time_http_request(f"{FASTAPI_BASE}/health")
        health_latencies.append(lat)
    h_stats = compute_stats(health_latencies)
    print(f"\n1. FastAPI /health Latency (5 runs):")
    print(f"   Mean: {h_stats['mean']:.2f} ms | Median: {h_stats['median']:.2f} ms | Min: {h_stats['min']:.2f} ms | Max: {h_stats['max']:.2f} ms | StdDev: {h_stats['std_dev']:.2f} ms")

    # 2. FastAPI Cold Latency
    # (FastAPI is already warm, but let's test a distinct coordinate for cold query if needed, or measure first request)
    cold_lat, cold_resp = time_http_request(f"{FASTAPI_BASE}/risk/assess", method="POST", data=TEST_COORDS)
    print(f"\n2. FastAPI /risk/assess First Call Latency: {cold_lat:.2f} ms")

    # 3. FastAPI Warm Latencies (5 runs)
    fastapi_warm = []
    for i in range(5):
        lat, resp = time_http_request(f"{FASTAPI_BASE}/risk/assess", method="POST", data=TEST_COORDS)
        fastapi_warm.append(lat)
        print(f"   Run {i+1}: {lat:.2f} ms")
    f_stats = compute_stats(fastapi_warm)
    print(f"   FastAPI Warm Summary:")
    print(f"   Mean: {f_stats['mean']:.2f} ms | Median: {f_stats['median']:.2f} ms | Min: {f_stats['min']:.2f} ms | Max: {f_stats['max']:.2f} ms | StdDev: {f_stats['std_dev']:.2f} ms")

    # 4. Spring Boot Full /api/risk/assess Latencies (5 runs)
    sb_warm = []
    for i in range(5):
        lat, resp = time_http_request(f"{SPRING_BOOT_BASE}/api/risk/assess", method="POST", data=TEST_COORDS)
        sb_warm.append(lat)
        print(f"   Run {i+1}: {lat:.2f} ms")
    sb_stats = compute_stats(sb_warm)
    print(f"\n4. Full Spring Boot /api/risk/assess Latency (5 runs):")
    print(f"   Mean: {sb_stats['mean']:.2f} ms | Median: {sb_stats['median']:.2f} ms | Min: {sb_stats['min']:.2f} ms | Max: {sb_stats['max']:.2f} ms | StdDev: {sb_stats['std_dev']:.2f} ms")

    # 5. PostGIS Query Latency
    postgis_latencies = []
    for _ in range(5):
        lat, _ = time_http_request(f"{SPRING_BOOT_BASE}/api/risk-zones/locate?latitude={TEST_COORDS['latitude']}&longitude={TEST_COORDS['longitude']}")
        postgis_latencies.append(lat)
    p_stats = compute_stats(postgis_latencies)
    print(f"\n5. PostGIS Point-in-Polygon Query Latency (5 runs):")
    print(f"   Mean: {p_stats['mean']:.2f} ms | Median: {p_stats['median']:.2f} ms | Min: {p_stats['min']:.2f} ms | Max: {p_stats['max']:.2f} ms | StdDev: {p_stats['std_dev']:.2f} ms")

    # Save baseline metrics to JSON for later comparison
    baseline_data = {
        "fastapi_health": h_stats,
        "fastapi_cold_ms": cold_lat,
        "fastapi_warm": f_stats,
        "spring_boot_full": sb_stats,
        "postgis": p_stats,
        "sample_response": resp
    }
    with open("scratch/baseline_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2)
    print("\nSaved baseline results to scratch/baseline_benchmark_results.json")


if __name__ == "__main__":
    run_benchmarks()
