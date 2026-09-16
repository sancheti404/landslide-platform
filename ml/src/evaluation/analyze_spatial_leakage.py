"""
Spatial Leakage Analysis for Sentinel-2 Satellite Image Patches.

Evaluates geographic distances and potential footprint overlap (1.28 km x 1.28 km)
between Train, Validation, and Test sets across Uttarakhand sample coordinates.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt


TRAIN_META_PATH = Path("ml/data/processed/splits/train_metadata.csv")
TEST_META_PATH = Path("ml/data/processed/splits/test_metadata.csv")
OUTPUT_CSV_PATH = Path("ml/reports/analysis/swin_spatial_leakage_analysis.csv")
OUTPUT_FIG_PATH = Path("ml/reports/figures/swin_spatial_distance_distribution.png")

FOOTPRINT_METERS = 1280.0  # 128 pixels * 10m/pixel = 1,280m = 1.28km


def latlon_to_ecef(lat, lon):
    """Convert lat/lon degrees to 3D Cartesian coordinates (meters) on sphere."""
    R = 6371000.0
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    x = R * np.cos(lat_r) * np.cos(lon_r)
    y = R * np.cos(lat_r) * np.sin(lon_r)
    z = R * np.sin(lat_r)
    return np.column_stack([x, y, z])


def run_spatial_leakage_analysis():
    print("=" * 70)
    print("SWIN SPATIAL LEAKAGE ANALYSIS")
    print("=" * 70)

    # 1. Load metadata
    train_meta_full = pd.read_csv(TRAIN_META_PATH)
    test_meta = pd.read_csv(TEST_META_PATH)

    # 2. Stratified train/val split (80/20, random_state=42)
    train_meta, val_meta = train_test_split(
        train_meta_full,
        test_size=0.20,
        random_state=42,
        stratify=train_meta_full["landslide"]
    )

    print(f"Split sizes: Train={len(train_meta)}, Val={len(val_meta)}, Test={len(test_meta)}")

    # 3. Build spatial indices (cKDTree in 3D ECEF space)
    train_xyz = latlon_to_ecef(train_meta["latitude"].values, train_meta["longitude"].values)
    val_xyz = latlon_to_ecef(val_meta["latitude"].values, val_meta["longitude"].values)
    test_xyz = latlon_to_ecef(test_meta["latitude"].values, test_meta["longitude"].values)

    train_tree = cKDTree(train_xyz)
    val_tree = cKDTree(val_xyz)

    # Query nearest train neighbor for each validation sample
    val_to_train_dist, val_to_train_idx = train_tree.query(val_xyz, k=1)

    # Query nearest train neighbor for each test sample
    test_to_train_dist, test_to_train_idx = train_tree.query(test_xyz, k=1)

    # Query nearest val neighbor for each test sample
    test_to_val_dist, test_to_val_idx = val_tree.query(test_xyz, k=1)

    # Combined test to train+val (training split pool)
    train_val_xyz = np.vstack([train_xyz, val_xyz])
    train_val_tree = cKDTree(train_val_xyz)
    test_to_trainval_dist, _ = train_val_tree.query(test_xyz, k=1)

    # Count overlaps (distance < FOOTPRINT_METERS)
    val_train_overlaps = np.sum(val_to_train_dist < FOOTPRINT_METERS)
    test_train_overlaps = np.sum(test_to_train_dist < FOOTPRINT_METERS)
    test_trainval_overlaps = np.sum(test_to_trainval_dist < FOOTPRINT_METERS)

    summary_records = [
        {
            "comparison": "Val -> Nearest Train",
            "source_samples": len(val_meta),
            "target_samples": len(train_meta),
            "overlapping_footprints (<1.28km)": int(val_train_overlaps),
            "overlap_percentage (%)": round(100.0 * val_train_overlaps / len(val_meta), 2),
            "min_distance_m": round(float(np.min(val_to_train_dist)), 2),
            "median_distance_m": round(float(np.median(val_to_train_dist)), 2),
            "mean_distance_m": round(float(np.mean(val_to_train_dist)), 2),
            "p25_distance_m": round(float(np.percentile(val_to_train_dist, 25)), 2),
            "p75_distance_m": round(float(np.percentile(val_to_train_dist, 75)), 2),
        },
        {
            "comparison": "Test -> Nearest Train",
            "source_samples": len(test_meta),
            "target_samples": len(train_meta),
            "overlapping_footprints (<1.28km)": int(test_train_overlaps),
            "overlap_percentage (%)": round(100.0 * test_train_overlaps / len(test_meta), 2),
            "min_distance_m": round(float(np.min(test_to_train_dist)), 2),
            "median_distance_m": round(float(np.median(test_to_train_dist)), 2),
            "mean_distance_m": round(float(np.mean(test_to_train_dist)), 2),
            "p25_distance_m": round(float(np.percentile(test_to_train_dist, 25)), 2),
            "p75_distance_m": round(float(np.percentile(test_to_train_dist, 75)), 2),
        },
        {
            "comparison": "Test -> Nearest Train+Val",
            "source_samples": len(test_meta),
            "target_samples": len(train_meta_full),
            "overlapping_footprints (<1.28km)": int(test_trainval_overlaps),
            "overlap_percentage (%)": round(100.0 * test_trainval_overlaps / len(test_meta), 2),
            "min_distance_m": round(float(np.min(test_to_trainval_dist)), 2),
            "median_distance_m": round(float(np.median(test_to_trainval_dist)), 2),
            "mean_distance_m": round(float(np.mean(test_to_trainval_dist)), 2),
            "p25_distance_m": round(float(np.percentile(test_to_trainval_dist, 25)), 2),
            "p75_distance_m": round(float(np.percentile(test_to_trainval_dist, 75)), 2),
        }
    ]

    summary_df = pd.DataFrame(summary_records)
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print("\nSpatial Leakage Summary Table:")
    print(summary_df.to_string())

    # Create visualization
    OUTPUT_FIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.hist(
        test_to_trainval_dist / 1000.0,
        bins=50,
        color="#2b5c8f",
        alpha=0.75,
        edgecolor="white",
        label="Test -> Nearest Train/Val (km)"
    )
    plt.axvline(
        FOOTPRINT_METERS / 1000.0,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"1.28 km Patch Footprint Threshold ({round(100.0 * test_trainval_overlaps / len(test_meta), 1)}% overlap)"
    )
    plt.title("Distribution of Nearest Distances from Test Points to Training Samples", fontsize=13, fontweight="bold")
    plt.xlabel("Distance to Nearest Training Sample (km)", fontsize=11)
    plt.ylabel("Number of Test Samples", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(OUTPUT_FIG_PATH, dpi=300)
    plt.close()
    print(f"\nSaved analysis results to {OUTPUT_CSV_PATH}")
    print(f"Saved distribution plot to {OUTPUT_FIG_PATH}")


if __name__ == "__main__":
    run_spatial_leakage_analysis()
