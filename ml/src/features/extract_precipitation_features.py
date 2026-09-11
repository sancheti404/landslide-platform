"""
Step 34G: Extract CHIRPS Long-Term Mean Annual Precipitation Features for Uttarakhand ML Samples.

Workflow:
    1. Load 11,046 ML sample coordinates from uttarakhand_ml_samples.csv.
    2. Access CHIRPS Daily precipitation (UCSB-CHG/CHIRPS/DAILY) in Google Earth Engine.
    3. Filter for the 10-year climatological baseline: 2014-01-01 to 2024-01-01.
    4. Calculate annual precipitation totals for each of the 10 calendar years.
    5. Compute the long-term mean of the annual totals (mean_annual_precipitation_mm).
    6. Sample precipitation values at 5,566 m resolution (~0.05 deg) in batches of 1,000.
    7. Left-merge back onto authoritative input dataframe to preserve all 11,046 rows and order.
    8. Perform strict validation on row counts, IDs, coordinates, labels, and precipitation values.
    9. Save to ml/data/processed/features/uttarakhand_ml_precipitation_features.csv.
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
    "ml/data/processed/features/uttarakhand_ml_precipitation_features.csv"
)

DATASET_ID = "UCSB-CHG/CHIRPS/DAILY"

BAND_NAME = "precipitation"

START_DATE = "2014-01-01"
END_DATE = "2024-01-01"

YEARS = list(range(2014, 2024))

# CHIRPS native spatial resolution is ~0.05 degrees (~5.5 km)
SCALE_METERS = 5566

BATCH_SIZE = 1000


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

def initialize_earth_engine():
    """Initialize Google Earth Engine with designated project ID."""
    print("Initializing Google Earth Engine...", flush=True)
    ee.Initialize(project=PROJECT_ID)
    print(f"Earth Engine initialized with project: {PROJECT_ID}", flush=True)


# ============================================================
# PRECIPITATION COMPOSITING
# ============================================================

def build_mean_annual_precipitation_image(region):
    """
    Build the long-term mean annual precipitation composite from CHIRPS Daily.
    
    1. Filters daily images between START_DATE and END_DATE.
    2. Sums daily precipitation for each calendar year (2014 to 2023).
    3. Computes the multi-year mean of annual totals in mm/year.
    """
    print(f"\nAccessing CHIRPS Daily dataset: {DATASET_ID}...", flush=True)
    daily_collection = (
        ee.ImageCollection(DATASET_ID)
        .filterDate(START_DATE, END_DATE)
        .filterBounds(region)
    )

    daily_count = daily_collection.size().getInfo()
    print(f"Total daily CHIRPS observations found ({START_DATE} to {END_DATE}): {daily_count:,}", flush=True)

    if daily_count == 0:
        raise RuntimeError("No CHIRPS images found for the specified date range and region.")

    print(f"Aggregating annual precipitation totals across {len(YEARS)} calendar years ({YEARS[0]} to {YEARS[-1]})...", flush=True)

    annual_images = []
    for y in YEARS:
        year_start = f"{y}-01-01"
        year_end = f"{y + 1}-01-01"
        annual_total = (
            daily_collection.filterDate(year_start, year_end)
            .select(BAND_NAME)
            .sum()
            .rename(BAND_NAME)
            .set("year", y)
        )
        annual_images.append(annual_total)

    annual_collection = ee.ImageCollection(annual_images)
    annual_count = annual_collection.size().getInfo()
    print(f"Number of annual precipitation totals created: {annual_count}", flush=True)

    if annual_count != len(YEARS):
        raise RuntimeError(f"Expected {len(YEARS)} annual images, but created {annual_count}")

    print("Computing mean across all 10 annual precipitation totals (mm/year)...", flush=True)
    mean_annual = (
        annual_collection.mean()
        .rename("mean_annual_precipitation_mm")
        .clip(region)
    )

    return mean_annual, daily_count, annual_count


# ============================================================
# SAMPLE CONVERSION
# ============================================================

def dataframe_to_feature_collection(df):
    """
    Convert a pandas DataFrame into an Earth Engine FeatureCollection.
    Preserves sample_id, latitude, longitude, and landslide label.
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

def extract_precipitation_batch(precip_image, batch_df):
    """
    Extract mean annual precipitation for one batch of sample coordinates.
    """
    points = dataframe_to_feature_collection(batch_df)

    sampled = precip_image.sampleRegions(
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
                "mean_annual_precipitation_mm": properties.get("mean_annual_precipitation_mm"),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    start_time = time.time()

    print("=" * 70, flush=True)
    print("STEP 34G — LONG-TERM PRECIPITATION FEATURE EXTRACTION", flush=True)
    print("=" * 70, flush=True)

    # Record input file mtime and size to verify it remains unmodified
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

    # Add a small buffer of ~0.1 deg (~10 km) to ensure edge cells are completely covered
    region = ee.Geometry.Rectangle([min_lon - 0.1, min_lat - 0.1, max_lon + 0.1, max_lat + 0.1])

    print("\nDynamic study region bounds:", flush=True)
    print(f"  Longitude: {min_lon:.6f} to {max_lon:.6f}", flush=True)
    print(f"  Latitude : {min_lat:.6f} to {max_lat:.6f}", flush=True)

    # --------------------------------------------------------
    # Build precipitation image
    # --------------------------------------------------------
    precip_image, daily_count, annual_count = build_mean_annual_precipitation_image(region)

    # --------------------------------------------------------
    # Batch extraction
    # --------------------------------------------------------
    print(f"\nExtracting precipitation values in batches (scale: {SCALE_METERS} m)...", flush=True)
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

        batch_result = extract_precipitation_batch(precip_image, batch_df)
        output_batches.append(batch_result)

        print(f"Extracted rows: {len(batch_result)}", flush=True)

    # Combine raw EE batch results
    raw_result = pd.concat(output_batches, ignore_index=True)
    ee_returned = len(raw_result)
    ee_missing = len(samples) - ee_returned

    if ee_missing > 0:
        print(
            f"\nNote: Earth Engine returned {ee_returned} sampled points; "
            f"{ee_missing} sample(s) had missing precipitation values.",
            flush=True,
        )
    else:
        print(f"\nAll {ee_returned:,} sample points returned data from Earth Engine.", flush=True)

    # --------------------------------------------------------
    # Merge back onto authoritative input samples
    # Preserves authoritative ordering, all 11,046 rows, and missing pixels become NaN
    # --------------------------------------------------------
    result = samples[["sample_id", "latitude", "longitude", "landslide"]].merge(
        raw_result[["sample_id", "mean_annual_precipitation_mm"]],
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
    expected_cols = ["sample_id", "latitude", "longitude", "landslide", "mean_annual_precipitation_mm"]
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

    # Check 14: Missing precipitation values
    missing_precip_count = int(result["mean_annual_precipitation_mm"].isna().sum())

    # Check 15: No +Inf or -Inf precipitation values
    precip_values = result["mean_annual_precipitation_mm"].values.astype(float)
    inf_pos = int(np.isposinf(precip_values).sum())
    inf_neg = int(np.isneginf(precip_values).sum())
    if inf_pos + inf_neg > 0:
        raise ValueError(f"Validation Failure: Inf values detected (+Inf: {inf_pos}, -Inf: {inf_neg})")

    # Check 16: All non-null precipitation values are >= 0
    non_null_precip = result["mean_annual_precipitation_mm"].dropna()
    negative_count = int((non_null_precip < 0).sum())
    if negative_count > 0:
        raise ValueError(f"Validation Failure: Found {negative_count} negative precipitation values")

    # Check 17: Annual aggregation period correctly implemented
    if annual_count != len(YEARS) or len(YEARS) != 10:
        raise ValueError(f"Validation Failure: Expected 10 annual aggregation periods, got {annual_count}")

    print("All strict validation checks PASSED successfully.", flush=True)

    # --------------------------------------------------------
    # Save output dataset
    # --------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved precipitation features to: {OUTPUT_FILE}", flush=True)

    # --------------------------------------------------------
    # FINAL TERMINAL REPORT
    # --------------------------------------------------------
    elapsed = time.time() - start_time

    print("\n" + "=" * 70, flush=True)
    print("STEP 34G COMPLETED", flush=True)
    print("=" * 70, flush=True)

    print(f"Output file path:                           {OUTPUT_FILE}")
    print(f"Dataset used:                               {DATASET_ID}")
    print(f"Time period:                                {START_DATE} to {END_DATE}")
    print(f"Number of annual periods:                   {annual_count} years ({YEARS[0]}-{YEARS[-1]})")
    print(f"Input samples:                              {len(samples):,}")
    print(f"Output samples:                             {len(result):,}")
    print(f"Unique sample IDs:                          {result['sample_id'].nunique():,}")
    print(f"Duplicate sample IDs:                       {dup_count}")
    print(f"Missing precipitation values:               {missing_precip_count}")
    print(f"Minimum mean annual precipitation (mm/year):{non_null_precip.min():.2f}")
    print(f"Maximum mean annual precipitation (mm/year):{non_null_precip.max():.2f}")
    print(f"Mean precipitation (mm/year):               {non_null_precip.mean():.2f}")
    print(f"Median precipitation (mm/year):             {non_null_precip.median():.2f}")
    print(f"Standard deviation (mm/year):               {non_null_precip.std():.2f}")
    print(f"Positive samples:                           {pos_out:,}")
    print(f"Negative samples:                           {neg_out:,}")
    print(f"Class balance:                              {'OK (50/50)' if pos_out == 5523 and neg_out == 5523 else 'ERROR'}")

    print("\nValidation Results Summary:")
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
    print("  14. Missing values counted and reported:       PASSED")
    print("  15. No +Inf or -Inf precipitation values:      PASSED")
    print("  16. All non-null precipitation values >= 0:    PASSED")
    print("  17. Annual aggregation period (10 yrs) valid:  PASSED")

    print(f"\nExecution time:                             {elapsed:.2f} seconds")
    print()
    print(">>> No machine learning model training was performed during Step 34G. <<<")
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    main()
