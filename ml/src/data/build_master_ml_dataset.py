"""
Step 35: Build Master Machine-Learning Feature Dataset for Uttarakhand Landslide Susceptibility Modeling.

Workflow:
    1. Load authoritative base ML dataset (uttarakhand_ml_samples.csv).
    2. Sequentially left-merge all extracted environmental feature datasets:
       - Terrain (elevation_m, slope_degrees, aspect_degrees)
       - Curvature (profile_curvature, plan_curvature)
       - Topographic Wetness Index (twi)
       - Sentinel-2 NDVI (ndvi)
       - ESA WorldCover LULC (lulc_class)
       - CHIRPS Long-Term Precipitation (mean_annual_precipitation_mm)
    3. Reorder columns to the authoritative schema.
    4. Run comprehensive validation suite (row counts, IDs, coordinates, labels, class balance, infs, missing values, file immutability).
    5. Save output to ml/data/processed/uttarakhand_master_ml_dataset.csv.
    6. Print comprehensive summary report.
"""

from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION AND CONSTANTS
# ============================================================

BASE_DATASET_PATH = Path("ml/data/processed/uttarakhand_ml_samples.csv")

FEATURE_DIR = Path("ml/data/processed/features")

OUTPUT_PATH = Path("ml/data/processed/uttarakhand_master_ml_dataset.csv")

EXPECTED_ROW_COUNT = 11046
EXPECTED_POS_COUNT = 5523
EXPECTED_NEG_COUNT = 5523

# Ordered list of feature sources and their target feature columns
FEATURE_SOURCES = [
    {
        "name": "Terrain",
        "file": FEATURE_DIR / "uttarakhand_ml_terrain_features.csv",
        "columns": ["elevation_m", "slope_degrees", "aspect_degrees"],
    },
    {
        "name": "Curvature",
        "file": FEATURE_DIR / "uttarakhand_ml_curvature_features.csv",
        "columns": ["profile_curvature", "plan_curvature"],
    },
    {
        "name": "TWI",
        "file": FEATURE_DIR / "uttarakhand_ml_twi_features.csv",
        "columns": ["twi"],
    },
    {
        "name": "NDVI",
        "file": FEATURE_DIR / "uttarakhand_ml_ndvi_features.csv",
        "columns": ["ndvi"],
    },
    {
        "name": "LULC",
        "file": FEATURE_DIR / "uttarakhand_ml_lulc_features.csv",
        "columns": ["lulc_class"],
    },
    {
        "name": "Precipitation",
        "file": FEATURE_DIR / "uttarakhand_ml_precipitation_features.csv",
        "columns": ["mean_annual_precipitation_mm"],
    },
]

# Authoritative final column order
FINAL_COLUMN_ORDER = [
    "sample_id",
    "latitude",
    "longitude",
    "elevation_m",
    "slope_degrees",
    "aspect_degrees",
    "profile_curvature",
    "plan_curvature",
    "twi",
    "ndvi",
    "lulc_class",
    "mean_annual_precipitation_mm",
    "landslide",
]

NUMERIC_FEATURE_COLUMNS = [
    "elevation_m",
    "slope_degrees",
    "aspect_degrees",
    "profile_curvature",
    "plan_curvature",
    "twi",
    "ndvi",
    "lulc_class",
    "mean_annual_precipitation_mm",
]


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    start_time = time.time()

    print("=" * 75, flush=True)
    print("STEP 35 — BUILD MASTER MACHINE-LEARNING FEATURE DATASET", flush=True)
    print("=" * 75, flush=True)

    # --------------------------------------------------------
    # 1. Record input files metadata for immutability verification
    # --------------------------------------------------------
    all_input_files = [BASE_DATASET_PATH] + [src["file"] for src in FEATURE_SOURCES]
    input_file_states_before = {}
    for f in all_input_files:
        if not f.exists():
            raise FileNotFoundError(f"Required input file missing: {f}")
        stat = f.stat()
        input_file_states_before[f] = (stat.st_size, stat.st_mtime)

    # --------------------------------------------------------
    # 2. Load authoritative base dataset
    # --------------------------------------------------------
    print(f"\nLoading authoritative base dataset: {BASE_DATASET_PATH}...", flush=True)
    base_df = pd.read_csv(BASE_DATASET_PATH)

    required_base_cols = {"sample_id", "latitude", "longitude", "landslide"}
    if not required_base_cols.issubset(base_df.columns):
        raise ValueError(f"Base dataset missing required columns: {required_base_cols - set(base_df.columns)}")

    if len(base_df) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Base dataset row count {len(base_df)} != expected {EXPECTED_ROW_COUNT}")

    if base_df["sample_id"].nunique() != EXPECTED_ROW_COUNT:
        raise ValueError("Base dataset sample_id values are not unique")

    base_pos = int((base_df["landslide"] == 1).sum())
    base_neg = int((base_df["landslide"] == 0).sum())
    if base_pos != EXPECTED_POS_COUNT or base_neg != EXPECTED_NEG_COUNT:
        raise ValueError(f"Base dataset class balance altered: pos={base_pos}, neg={base_neg}")

    print(f"Authoritative base dataset loaded: {len(base_df):,} samples", flush=True)
    print(f"  Positive samples (landslide = 1): {base_pos:,}", flush=True)
    print(f"  Negative samples (landslide = 0): {base_neg:,}", flush=True)

    # Start merging onto authoritative base copy
    master_df = base_df[["sample_id", "latitude", "longitude", "landslide"]].copy()

    # --------------------------------------------------------
    # 3. Sequentially Left-Merge Each Feature File
    # --------------------------------------------------------
    print("\nMerging feature datasets...", flush=True)

    for src in FEATURE_SOURCES:
        name = src["name"]
        file_path = src["file"]
        feature_cols = src["columns"]

        print(f"\nProcessing [{name}] features from: {file_path.name}")
        feat_df = pd.read_csv(file_path)

        # Validate sample_id existence and uniqueness in feature file
        if "sample_id" not in feat_df.columns:
            raise ValueError(f"Feature file '{file_path.name}' is missing 'sample_id' column")

        feat_id_count = len(feat_df)
        feat_id_unique = feat_df["sample_id"].nunique()
        if feat_id_count != feat_id_unique:
            raise ValueError(f"Feature file '{file_path.name}' contains duplicate sample_id values")

        # Verify sample_id set parity
        base_ids = set(base_df["sample_id"])
        feat_ids = set(feat_df["sample_id"])
        missing_ids = base_ids - feat_ids
        unexpected_ids = feat_ids - base_ids

        if missing_ids:
            print(f"  Warning: {len(missing_ids)} base sample IDs missing in {file_path.name} (will be NaN)")
        if unexpected_ids:
            print(f"  Warning: {len(unexpected_ids)} unexpected sample IDs in {file_path.name} (will be ignored)")

        # Verify requested feature columns exist
        missing_feats = set(feature_cols) - set(feat_df.columns)
        if missing_feats:
            raise ValueError(f"Feature file '{file_path.name}' is missing columns: {missing_feats}")

        # Check sample_id uniqueness before merge
        if master_df["sample_id"].nunique() != len(master_df):
            raise ValueError("Pre-merge master_df has non-unique sample IDs")

        # Perform left join with 1:1 validation (ignoring coordinates/landslide in feature file)
        merge_subset = feat_df[["sample_id"] + feature_cols]
        master_df = master_df.merge(
            merge_subset,
            on="sample_id",
            how="left",
            validate="1:1",
        )

        # Check sample_id uniqueness and row count after merge
        if len(master_df) != EXPECTED_ROW_COUNT:
            raise ValueError(f"Row count changed after merging {name}: got {len(master_df)}")
        if master_df["sample_id"].nunique() != EXPECTED_ROW_COUNT:
            raise ValueError(f"Duplicate sample IDs created after merging {name}")

        print(f"  Successfully merged columns: {feature_cols}")
        for col in feature_cols:
            col_nan = int(master_df[col].isna().sum())
            print(f"    - {col:<30s}: {len(master_df) - col_nan:>6,d} valid, {col_nan:>4d} missing (NaN)")

    # --------------------------------------------------------
    # 4. Enforce Authoritative Column Order
    # --------------------------------------------------------
    print(f"\nReordering columns to authoritative schema ({len(FINAL_COLUMN_ORDER)} columns)...", flush=True)
    extra_cols = set(master_df.columns) - set(FINAL_COLUMN_ORDER)
    missing_final_cols = set(FINAL_COLUMN_ORDER) - set(master_df.columns)

    if extra_cols:
        raise ValueError(f"Unexpected extra columns in master dataset: {extra_cols}")
    if missing_final_cols:
        raise ValueError(f"Missing required final columns in master dataset: {missing_final_cols}")

    master_df = master_df[FINAL_COLUMN_ORDER]

    # --------------------------------------------------------
    # 5. STRICT VALIDATION SUITE
    # --------------------------------------------------------
    print("\nRunning comprehensive validation checks...", flush=True)

    # 1. Final row count
    if len(master_df) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Validation Failure: Row count {len(master_df)} != {EXPECTED_ROW_COUNT}")

    # 2 & 3. sample_id uniqueness
    if master_df["sample_id"].nunique() != EXPECTED_ROW_COUNT:
        raise ValueError("Validation Failure: sample_id values are not unique")
    dup_sample_ids = int(master_df["sample_id"].duplicated().sum())
    if dup_sample_ids != 0:
        raise ValueError(f"Validation Failure: Found {dup_sample_ids} duplicate sample IDs")

    # 4. Exact sample_id ordering
    if not (master_df["sample_id"].values == base_df["sample_id"].values).all():
        raise ValueError("Validation Failure: Sample ID ordering does not match authoritative base dataset")

    # 5. Latitude exact match
    if not np.allclose(master_df["latitude"].values, base_df["latitude"].values, atol=1e-7):
        raise ValueError("Validation Failure: Final latitude coordinates do not match base dataset")

    # 6. Longitude exact match
    if not np.allclose(master_df["longitude"].values, base_df["longitude"].values, atol=1e-7):
        raise ValueError("Validation Failure: Final longitude coordinates do not match base dataset")

    # 7. Landslide labels exact match
    if not (master_df["landslide"].values == base_df["landslide"].values).all():
        raise ValueError("Validation Failure: Final landslide labels do not match base dataset")

    # 8. Landslide values strictly {0, 1}
    unique_labels = set(master_df["landslide"].unique())
    if not unique_labels.issubset({0, 1}):
        raise ValueError(f"Validation Failure: Landslide labels contain unexpected values: {unique_labels}")

    # 9. Class balance verification
    pos_count = int((master_df["landslide"] == 1).sum())
    neg_count = int((master_df["landslide"] == 0).sum())
    if pos_count != EXPECTED_POS_COUNT or neg_count != EXPECTED_NEG_COUNT:
        raise ValueError(f"Validation Failure: Class counts altered: pos={pos_count}, neg={neg_count}")

    # 10. Missing values per column
    missing_counts = master_df.isna().sum().to_dict()

    # 11. Infinite values check per numeric column
    inf_counts = {}
    for col in NUMERIC_FEATURE_COLUMNS + ["latitude", "longitude"]:
        col_vals = master_df[col].values.astype(float)
        pos_inf = int(np.isposinf(col_vals).sum())
        neg_inf = int(np.isneginf(col_vals).sum())
        total_inf = pos_inf + neg_inf
        inf_counts[col] = total_inf
        if total_inf > 0:
            raise ValueError(f"Validation Failure: Column '{col}' contains {total_inf} infinite values")

    # 13 & 14. Column validation
    if list(master_df.columns) != FINAL_COLUMN_ORDER:
        raise ValueError("Validation Failure: Column order does not match authoritative schema")

    # 15. Verify input files were not modified
    for f in all_input_files:
        stat_after = f.stat()
        before_size, before_mtime = input_file_states_before[f]
        if (stat_after.st_size != before_size) or (stat_after.st_mtime != before_mtime):
            raise ValueError(f"Validation Failure: Input file '{f.name}' was modified during execution!")

    print("All strict validation checks PASSED successfully.", flush=True)

    # --------------------------------------------------------
    # 6. Save Master Dataset
    # --------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved master ML dataset to: {OUTPUT_PATH}", flush=True)

    # --------------------------------------------------------
    # 7. Compute Numeric Feature Statistics
    # --------------------------------------------------------
    stats_data = []
    for col in NUMERIC_FEATURE_COLUMNS:
        series = master_df[col].dropna()
        stats_data.append({
            "Feature": col,
            "Count": len(series),
            "Missing": missing_counts[col],
            "Min": series.min(),
            "Max": series.max(),
            "Mean": series.mean(),
            "Median": series.median(),
            "StdDev": series.std(),
        })
    stats_df = pd.DataFrame(stats_data)

    # --------------------------------------------------------
    # 8. FINAL TERMINAL REPORT
    # --------------------------------------------------------
    elapsed = time.time() - start_time

    print("\n" + "=" * 75, flush=True)
    print("STEP 35 COMPLETED — MASTER ML FEATURE DATASET SUMMARY", flush=True)
    print("=" * 75, flush=True)

    print(f"MASTER_DATASET_ROWS:        {len(master_df):,}")
    print(f"POSITIVE_COUNT:             {pos_count:,}")
    print(f"NEGATIVE_COUNT:             {neg_count:,}")
    print(f"DUPLICATE_SAMPLE_IDS:       {dup_sample_ids}")

    print("\nMISSING_VALUES_PER_COLUMN:")
    for col in FINAL_COLUMN_ORDER:
        print(f"  {col:<30s}: {missing_counts[col]:>5d} missing")

    print("\nINFINITE_VALUES_PER_COLUMN:")
    for col, count in inf_counts.items():
        print(f"  {col:<30s}: {count:>5d} infinite")

    print("\nFINAL_COLUMNS:")
    for idx, col in enumerate(FINAL_COLUMN_ORDER, start=1):
        print(f"  {idx:>2d}. {col}")

    print("\nNUMERIC_FEATURE_STATISTICS:")
    print("-" * 105)
    print(f"{'Feature':<30} {'Valid':<8} {'Missing':<8} {'Min':<11} {'Max':<11} {'Mean':<11} {'Median':<11} {'StdDev':<11}")
    print("-" * 105)
    for _, row in stats_df.iterrows():
        print(
            f"{row['Feature']:<30} "
            f"{row['Count']:<8d} "
            f"{row['Missing']:<8d} "
            f"{row['Min']:<11.4f} "
            f"{row['Max']:<11.4f} "
            f"{row['Mean']:<11.4f} "
            f"{row['Median']:<11.4f} "
            f"{row['StdDev']:<11.4f}"
        )
    print("-" * 105)

    print(f"\nExecution Time:             {elapsed:.2f} seconds")
    print()
    print("Step 35 completed successfully. No ML model training was performed.")
    print("=" * 75 + "\n", flush=True)


if __name__ == "__main__":
    main()
