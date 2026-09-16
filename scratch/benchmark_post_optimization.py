"""
Post-Optimization Benchmark, Numerical Regression, and Concurrency Verification.
Uttarakhand Landslide Intelligence Platform — Step 43 Production Hardening.
"""

import concurrent.futures
import json
import statistics
import time
import requests

FASTAPI_URL = "http://127.0.0.1:8000"
SPRING_BOOT_URL = "http://127.0.0.1:8080"
TEST_COORD = {"latitude": 30.529505, "longitude": 79.085957, "timestamp": "2023-07-15"}

def run_benchmarks():
    print("=== STEP 43 POST-OPTIMIZATION BENCHMARK & VERIFICATION ===")

    # 1. Health and Readiness Probes
    print("\n1. Testing Health & Readiness Probes...")
    resp_live = requests.get(f"{FASTAPI_URL}/health/live")
    assert resp_live.status_code == 200, f"Health live failed: {resp_live.status_code}"
    print(f"  [PASS] /health/live: {resp_live.json()}")

    resp_ready = requests.get(f"{FASTAPI_URL}/health/ready")
    assert resp_ready.status_code == 200, f"Health ready failed: {resp_ready.status_code}"
    print(f"  [PASS] /health/ready: {resp_ready.json()}")

    # 2. FastAPI Warm Latency Benchmark
    print("\n2. Benchmarking FastAPI /risk/assess (Warm Cache)...")
    # Initial request to populate cache
    r0 = requests.post(f"{FASTAPI_URL}/risk/assess", json=TEST_COORD, headers={"X-Request-ID": "post-opt-warmup"})
    assert r0.status_code == 200, f"Warmup failed: {r0.status_code} - {r0.text}"
    req_id_ret = r0.headers.get("X-Request-ID")
    assert req_id_ret == "post-opt-warmup", f"X-Request-ID mismatch: {req_id_ret}"

    fastapi_warm_times = []
    sample_fastapi_resp = None
    for i in range(5):
        t0 = time.perf_counter()
        r = requests.post(f"{FASTAPI_URL}/risk/assess", json=TEST_COORD, headers={"X-Request-ID": f"bench-{i}"})
        elapsed = (time.perf_counter() - t0) * 1000.0
        fastapi_warm_times.append(elapsed)
        if i == 0:
            sample_fastapi_resp = r.json()
        print(f"  Run {i+1}: {elapsed:.2f} ms (timings: {r.json().get('timings_ms')})")

    # 3. Spring Boot Full E2E Latency Benchmark
    print("\n3. Benchmarking Spring Boot /api/risk/assess (Full E2E + PostGIS)...")
    sb_warm_times = []
    sample_sb_resp = None
    for i in range(5):
        t0 = time.perf_counter()
        r = requests.post(f"{SPRING_BOOT_URL}/api/risk/assess", json=TEST_COORD, headers={"X-Request-ID": f"sb-bench-{i}"})
        elapsed = (time.perf_counter() - t0) * 1000.0
        sb_warm_times.append(elapsed)
        assert r.status_code == 200, f"Spring Boot failed: {r.status_code} - {r.text}"
        assert r.headers.get("X-Request-ID") == f"sb-bench-{i}"
        if i == 0:
            sample_sb_resp = r.json()
        print(f"  Run {i+1}: {elapsed:.2f} ms")

    # 4. Numerical Regression Verification against Baseline
    print("\n4. Numerical Regression Verification against Pre-Optimization Baseline...")
    with open("scratch/baseline_benchmark_results.json", "r") as f:
        baseline_data = json.load(f)
    baseline_resp = baseline_data["sample_response"]

    keys_to_compare = [
        "xgboost_probability",
        "swin_probability",
        "static_visual_fusion_score",
        "rainfall_3d_mm",
        "rainfall_7d_mm",
        "rainfall_14d_mm",
        "rainfall_30d_mm",
        "maximum_daily_rainfall_mm",
        "rainfall_anomaly",
        "dynamic_rainfall_trigger_score",
        "operational_landslide_risk_score",
        "risk_level",
        "trigger_indicator",
    ]

    all_matched = True
    for k in keys_to_compare:
        base_v = baseline_resp[k]
        fastapi_v = sample_fastapi_resp[k]
        sb_v = sample_sb_resp[k]
        if base_v != fastapi_v or base_v != sb_v:
            print(f"  [MISMATCH] {k}: baseline={base_v}, fastapi={fastapi_v}, sb={sb_v}")
            all_matched = False
        else:
            print(f"  [MATCH] {k}: {base_v} == {fastapi_v} (FastAPI) == {sb_v} (Spring Boot)")

    assert all_matched, "Regression check failed: Outputs do not match baseline exactly!"
    print("  --> ALL ML SIGNALS AND RISK SCORES 100% NUMERICALLY IDENTICAL TO BASELINE!")

    # 5. Concurrency Test (5 Concurrent Requests)
    print("\n5. Testing 5-Request Concurrency (Thread Safety & Cache Integrity)...")
    def send_concurrent_request(idx):
        req_id = f"concur-test-{idx}"
        t0 = time.perf_counter()
        resp = requests.post(f"{SPRING_BOOT_URL}/api/risk/assess", json=TEST_COORD, headers={"X-Request-ID": req_id})
        elapsed = (time.perf_counter() - t0) * 1000.0
        return idx, resp.status_code, elapsed, resp.headers.get("X-Request-ID"), resp.json()["operational_landslide_risk_score"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_concurrent_request, i) for i in range(5)]
        results = [f.result() for f in futures]

    for idx, status, elapsed, ret_id, score in results:
        print(f"  Concurrent Worker {idx}: status={status}, latency={elapsed:.2f} ms, req_id={ret_id}, score={score}")
        assert status == 200, f"Worker {idx} failed"
        assert ret_id == f"concur-test-{idx}", f"Worker {idx} ID mismatch"
        assert score == 1.0, f"Worker {idx} score corrupted"
    print("  --> CONCURRENCY TEST PASSED: 0 race conditions, 0 cache corruptions.")

    # 6. Save Comparison Summary
    comparison = {
        "fastapi_warm_post_opt": {
            "min": min(fastapi_warm_times),
            "max": max(fastapi_warm_times),
            "mean": statistics.mean(fastapi_warm_times),
            "median": statistics.median(fastapi_warm_times),
            "std_dev": statistics.stdev(fastapi_warm_times),
        },
        "spring_boot_warm_post_opt": {
            "min": min(sb_warm_times),
            "max": max(sb_warm_times),
            "mean": statistics.mean(sb_warm_times),
            "median": statistics.median(sb_warm_times),
            "std_dev": statistics.stdev(sb_warm_times),
        },
        "baseline_comparison": {
            "fastapi_warm_mean_baseline_ms": baseline_data["fastapi_warm"]["mean"],
            "fastapi_warm_mean_post_opt_ms": statistics.mean(fastapi_warm_times),
            "fastapi_speedup_factor": round(baseline_data["fastapi_warm"]["mean"] / statistics.mean(fastapi_warm_times), 1),
            "spring_boot_mean_baseline_ms": baseline_data["spring_boot_full"]["mean"],
            "spring_boot_mean_post_opt_ms": statistics.mean(sb_warm_times),
            "spring_boot_speedup_factor": round(baseline_data["spring_boot_full"]["mean"] / statistics.mean(sb_warm_times), 1),
        },
        "sample_response": sample_sb_resp,
    }

    with open("scratch/post_optimization_benchmark_results.json", "w") as f:
        json.dump(comparison, f, indent=2)

    print("\n=== POST-OPTIMIZATION BENCHMARK RESULTS ===")
    print(f"FastAPI Warm Latency: Mean = {statistics.mean(fastapi_warm_times):.2f} ms (Baseline: {baseline_data['fastapi_warm']['mean']:.2f} ms) -> {comparison['baseline_comparison']['fastapi_speedup_factor']}x speedup!")
    print(f"Spring Boot E2E Latency: Mean = {statistics.mean(sb_warm_times):.2f} ms (Baseline: {baseline_data['spring_boot_full']['mean']:.2f} ms) -> {comparison['baseline_comparison']['spring_boot_speedup_factor']}x speedup!")


if __name__ == "__main__":
    run_benchmarks()
