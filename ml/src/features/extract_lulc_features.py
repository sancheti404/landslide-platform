"""
Step 34F: Extract ESA WorldCover 2021 LULC features for Uttarakhand ML samples.

Workflow:
    1. Load 11,046 ML sample coordinates from uttarakhand_ml_samples.csv.
    2. Access ESA WorldCover 2021 (ESA/WorldCover/v200) in Google Earth Engine.
    3. Determine the study region bounding box dynamically from sample coordinates.
    4. Select the 'Map' band and rename to 'lulc_class'.
    5. Extract categorical LULC class at 10m scale using batch processing.
    6. Merge sampled LULC values back onto authoritative input coordinates by sample_id.
    7. Perform strict validation on row counts, IDs, coordinates, labels, and valid class codes.
    8. Save output to ml/data/processed/features/uttarakhand_ml_lulc_features.csv.
"""

from pathlib import Path
import sys
import time

import ee
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION AND CONSTANTS
# ============================================================

PROJECT_ID = "landslide-platform-508308"

INPUT_FILE = Path(
    "ml/data/processed/uttarakhand_ml_samples.csv"
)

OUTPUT_FILE = Path(
    "ml/data/processed/features/uttarakhand_ml_lulc_features.csv"
)

DATASET_ID = "ESA/WorldCover/v200"

BAND_NAME = "Map"

# ESA WorldCover spatial resolution in meters
SCALE_METERS = 10

# Batch size for Earth Engine feature sampling
BATCH_SIZE = 1000

# Valid ESA WorldCover categorical class codes
VALID_LULC_CLASSES = {
    10,   # Tree cover
    20,   # Shrubland
    30,   # Grassland
    40,   # Cropland
    50,   # Built-up
    60,   # Bare / sparse vegetation
    70,   # Snow and ice
    80,   # Permanent water bodies
    90,   # Herbaceous wetland
    95,   # Mangroves
    100,  # Moss and lichen
}

LULC_CLASS_NAMES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

def initialize_earth_engine():
    """Initialize Google Earth Engine."""
    print("Initializing Google Earth Engine...", flush=True)
    ee.Initialize(project=PROJECT_ID)
    print(f"Earth Engine initialized with project: {PROJECT_ID}", flush=True)


# ============================================================
# LULC DATASET INITIALIZATION
# ============================================================

def load_lulc_image(region):
    """
    Load ESA WorldCover 2021 image from Earth Engine and prepare the LULC band.
    """
    print(f"Loading ESA WorldCover dataset: {DATASET_ID}...", flush=True)
    collection = ee.ImageCollection(DATASET_ID)
    image = collection.first()

    # Select the Map band and rename to lulc_class
    lulc_image = image.select([BAND_NAME], ["lulc_class"]).clip(region)
    print(f"Selected band '{BAND_NAME}' renamed to 'lulc_class' at {SCALE_METERS}m resolution.", flush=True)
    return lulc_image


# ============================================================
# SAMPLE CONVERSION
# ============================================================

def dataframe_to_feature_collection(df):
    """
    Convert a pandas DataFrame into an Earth Engine FeatureCollection.
    Preserves sample_id, latitude, longitude, and landslide.
    """
    features = []
    for row in df.itertuples(index=False):
        feature = ee.Feature(
            ee.Geometry.Point([float(row.longitude), float(row.latitude)]),
            {
                "sample_id": str(row.sample_id),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "landslide": int(row.landslide),
            },
        )
        features.append(feature)
    return ee.FeatureCollection(features)


# ============================================================
# BATCH FEATURE EXTRACTION
# ============================================================

def extract_lulc_batch(lulc_image, batch_df):
    """
    Extract categorical LULC values for one batch of sample coordinates.
    """
    points = dataframe_to_feature_collection(batch_df)

    sampled = lulc_image.sampleRegions(
        collection=points,
        scale=SCALE_METERS,
        geometries=False,
    )

    results = sampled.getInfo()
    rows = []

    for feature in results.get("features", []):
        properties = feature["properties"]
        rows.append(
            {
                "sample_id": properties["sample_id"],
                "latitude": properties["latitude"],
                "longitude": properties["longitude"],
                "landslide": properties["landslide"],
                "lulc_class": properties.get("lulc_class"),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    start_time = time.time()

    print("=" * 70, flush=True)
    print("STEP 34F — LAND USE / LAND COVER (LULC) FEATURE EXTRACTION", flush=True)
    print("=" * 70, flush=True)

    # Record initial hash or state of input file to verify it is not modified
    input_file_mtime_before = INPUT_FILE.stat().st_mtime
    input_file_bytes_before = INPUT_FILE.stat().st_size

    # --------------------------------------------------------
    # Initialize Earth Engine
    # --------------------------------------------------------
    initialize_earth_engine()

    # --------------------------------------------------------
    # Load ML samples
    # --------------------------------------------------------
    print("\nLoading ML samples...", flush=True)
    samples = pd.read_csv(INPUT_FILE)

    required_columns = {"sample_id", "latitude", "longitude", "landslide"}
    missing_columns = required_columns - set(samples.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in input: {missing_columns}")

    if len(samples) != 11046:
        raise ValueError(f"Expected 11,046 input samples, found {len(samples)}")

    pos_in = int((samples["landslide"] == 1).sum())
    neg_in = int((samples["landslide"] == 0).sum())
    if pos_in != 5523 or neg_in != 5523:
        raise ValueError(f"Input class balance unexpected: pos={pos_in}, neg={neg_in}")

    print(f"Input samples loaded: {len(samples):,}", flush=True)
    print(f"  Positive (landslide=1): {pos_in:,}", flush=True)
    print(f"  Negative (landslide=0): {neg_in:,}", flush=True)

    # --------------------------------------------------------
    # Determine study region bounds dynamically
    # --------------------------------------------------------
    min_lon = float(samples["longitude"].min())
    max_lon = float(samples["longitude"].max())
    min_lat = float(samples["latitude"].min())
    max_lat = float(samples["latitude"].max())

    region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

    print("\nDynamic study region bounds:", flush=True)
    print(f"  Longitude: {min_lon:.6f} to {max_lon:.6f}", flush=True)
    print(f"  Latitude : {min_lat:.6f} to {max_lat:.6f}", flush=True)

    # --------------------------------------------------------
    # Load ESA WorldCover image
    # --------------------------------------------------------
    lulc_image = load_lulc_image(region)

    # --------------------------------------------------------
    # Batch extraction
    # --------------------------------------------------------
    print("\nExtracting LULC values in batches...", flush=True)
    total_batches = (len(samples) + BATCH_SIZE - 1) // BATCH_SIZE
    output_batches = []

    for batch_number, start_index in enumerate(
        range(0, len(samples), BATCH_SIZE),
        start=1,
    ):
        end_index = min(start_index + BATCH_SIZE, len(samples))
        batch_df = samples.iloc[start_index:end_index]

        print(
            f"Processing batch {batch_number}/{total_batches} ({len(batch_df)} samples)...",
            end=" ",
            flush=True,
        )

        batch_result = extract_lulc_batch(lulc_image, batch_df)
        output_batches.append(batch_result)

        print(f"Extracted rows: {len(batch_result)}", flush=True)

    # Combine raw EE batch results
    raw_result = pd.concat(output_batches, ignore_index=True)
    ee_returned = len(raw_result)
    ee_missing = len(samples) - ee_returned

    if ee_missing > 0:
        print(
            f"\nNote: Earth Engine returned {ee_returned} sampled points; "
            f"{ee_missing} sample(s) had missing/unmapped pixels.",
            flush=True,
        )
    else:
        print(f"\nAll {ee_returned:,} sample points returned data from Earth Engine.", flush=True)

    # --------------------------------------------------------
    # Merge back onto authoritative input samples
    # Preserves authoritative ordering, all 11,046 rows, and missing pixels become NaN
    # --------------------------------------------------------
    result = samples[["sample_id", "latitude", "longitude", "landslide"]].merge(
        raw_result[["sample_id", "lulc_class"]],
        on="sample_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # STRICT VALIDATION
    # --------------------------------------------------------
    print("\nRunning strict validation checks...", flush=True)

    # Check 1 & 3: Input and output row count
    if len(result) != len(samples):
        raise ValueError(
            f"Validation Failure: Row count mismatch. Expected {len(samples)}, got {len(result)}"
        )

    # Check 2: Required columns exist
    expected_cols = ["sample_id", "latitude", "longitude", "landslide", "lulc_class"]
    if list(result.columns) != expected_cols:
        raise ValueError(
            f"Validation Failure: Output columns {list(result.columns)} do not match expected {expected_cols}"
        )

    # Check 4 & 5: sample_id uniqueness
    if result["sample_id"].nunique() != len(samples):
        raise ValueError(
            f"Validation Failure: Unique sample IDs ({result['sample_id'].nunique()}) != total rows ({len(samples)})"
        )
    dup_count = int(result["sample_id"].duplicated().sum())
    if dup_count != 0:
        raise ValueError(f"Validation Failure: Found {dup_count} duplicate sample IDs")

    # Check 6 & 7: Sample ID set equality
    expected_ids = set(samples["sample_id"])
    actual_ids = set(result["sample_id"])
    missing_ids = expected_ids - actual_ids
    if missing_ids:
        raise ValueError(f"Validation Failure: Missing {len(missing_ids)} sample IDs in output")
    unexpected_ids = actual_ids - expected_ids
    if unexpected_ids:
        raise ValueError(f"Validation Failure: Unexpected {len(unexpected_ids)} sample IDs in output")

    # Check 8: Latitude integrity
    if not np.allclose(result["latitude"].values, samples["latitude"].values, atol=1e-6):
        raise ValueError("Validation Failure: Latitude coordinates altered from input")

    # Check 9: Longitude integrity
    if not np.allclose(result["longitude"].values, samples["longitude"].values, atol=1e-6):
        raise ValueError("Validation Failure: Longitude coordinates altered from input")

    # Check 10: Landslide labels match original
    if not (result["landslide"].values == samples["landslide"].values).all():
        raise ValueError("Validation Failure: Landslide labels altered from input")

    # Check 11: Landslide labels strictly {0, 1}
    unique_labels = set(result["landslide"].unique())
    if not unique_labels.issubset({0, 1}):
        raise ValueError(f"Validation Failure: Invalid landslide labels: {unique_labels}")

    # Check 12: Class balance preserved
    pos_out = int((result["landslide"] == 1).sum())
    neg_out = int((result["landslide"] == 0).sum())
    if pos_out != 5523 or neg_out != 5523:
        raise ValueError(
            f"Validation Failure: Class balance altered: positive={pos_out}, negative={neg_out}"
        )

    # Check 13: Input CSV remains unmodified
    input_file_mtime_after = INPUT_FILE.stat().st_mtime
    input_file_bytes_after = INPUT_FILE.stat().st_size
    if (input_file_mtime_before != input_file_mtime_after) or (input_file_bytes_before != input_file_bytes_after):
        raise ValueError("Validation Failure: Input CSV file was modified during execution!")

    # Check 14: Missing LULC values
    missing_lulc_count = int(result["lulc_class"].isna().sum())

    # Check 15: Valid ESA WorldCover class codes
    non_null_lulc = result["lulc_class"].dropna()
    unique_extracted_classes = set(non_null_lulc.astype(int).unique())
    invalid_classes = unique_extracted_classes - VALID_LULC_CLASSES
    if invalid_classes:
        raise ValueError(
            f"Validation Failure: Encountered invalid ESA WorldCover class codes: {invalid_classes}"
        )

    print("All strict validation checks PASSED successfully.", flush=True)

    # Format lulc_class as nullable integer so CSV contains integer class codes
    if missing_lulc_count == 0:
        result["lulc_class"] = result["lulc_class"].astype(int)
    else:
        result["lulc_class"] = result["lulc_class"].astype("Int64")

    # --------------------------------------------------------
    # Save output dataset
    # --------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved LULC features to: {OUTPUT_FILE}", flush=True)

    # --------------------------------------------------------
    # FINAL TERMINAL REPORT
    # --------------------------------------------------------
    elapsed = time.time() - start_time

    print("\n" + "=" * 70, flush=True)
    print("STEP 34F COMPLETED", flush=True)
    print("=" * 70, flush=True)

    print(f"Output file path:       {OUTPUT_FILE}")
    print(f"Input sample count:     {len(samples):,}")
    print(f"Output sample count:    {len(result):,}")
    print(f"Unique sample IDs:      {result['sample_id'].nunique():,}")
    print(f"Duplicate sample IDs:   {dup_count}")
    print(f"Missing LULC values:    {missing_lulc_count}")
    print(f"Positive samples:       {pos_out:,}")
    print(f"Negative samples:       {neg_out:,}")
    print(f"Unique LULC classes:    {len(unique_extracted_classes)}")

    print("\nLULC Class Distribution:")
    print("-" * 65)
    print(f"{'Code':<6} {'Class Name':<26} {'Count':<10} {'Percentage':<10}")
    print("-" * 65)
    val_counts = result["lulc_class"].value_counts(dropna=False).sort_index()
    for cls_val, count in val_counts.items():
        if pd.isna(cls_val):
            print(f"{'NaN':<6} {'[Missing / Unmapped]':<26} {count:<10,d} {count/len(result)*100:>6.2f}%")
        else:
            cls_int = int(cls_val)
            name = LULC_CLASS_NAMES.get(cls_int, "Unknown")
            print(f"{cls_int:<6d} {name:<26} {count:<10,d} {count/len(result)*100:>6.2f}%")
    print("-" * 65)

    print("\nAll Validation Results:")
    print("  1. Input sample count is 11,046:               PASSED")
    print("  2. Required input columns present:             PASSED")
    print("  3. Output row count equals input (11,046):     PASSED")
    print("  4. Sample IDs are unique:                      PASSED")
    print("  5. Duplicate sample ID count is 0:             PASSED")
    print("  6. Every input sample ID present in output:    PASSED")
    print("  7. No unexpected sample IDs in output:         PASSED")
    print("  8. Latitude unchanged for every sample:        PASSED")
    print("  9. Longitude unchanged for every sample:       PASSED")
    print("  10. Landslide labels unchanged:                PASSED")
    print("  11. Landslide values strictly {0, 1}:          PASSED")
    print("  12. Class balance preserved (5523 / 5523):     PASSED")
    print("  13. Input CSV remained unmodified:             PASSED")
    print("  14. Missing LULC values counted and reported:  PASSED")
    print("  15. All classes match valid WorldCover codes:  PASSED")

    print(f"\nExecution time:         {elapsed:.2f} seconds")
    print()
    print(">>> No machine learning model training was performed during Step 34F. <<<")
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    main()
