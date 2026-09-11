"""
Step 34E: Extract Sentinel-2 NDVI features for Uttarakhand ML samples.

Workflow:
    1. Load 11,046 ML sample coordinates.
    2. Access Sentinel-2 Surface Reflectance Harmonized.
    3. Apply cloud filtering and cloud masking.
    4. Calculate NDVI at 10 m resolution.
    5. Create a temporal median NDVI composite.
    6. Extract NDVI for every ML sample.
    7. Validate and save the output CSV.
"""

from pathlib import Path
import time

import ee
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = "landslide-platform-508308"

INPUT_FILE = Path(
    "ml/data/processed/uttarakhand_ml_samples.csv"
)

OUTPUT_FILE = Path(
    "ml/data/processed/features/uttarakhand_ml_ndvi_features.csv"
)

# Use a full-year composite.
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"

# Sentinel-2 scene-level cloud filter.
MAX_CLOUD_PERCENTAGE = 30

# Earth Engine sampling scale in meters.
SCALE_METERS = 10

# Number of samples per Earth Engine request.
BATCH_SIZE = 1000


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

def initialize_earth_engine():
    """Initialize Google Earth Engine."""

    print("Initializing Google Earth Engine...")

    ee.Initialize(project=PROJECT_ID)

    print(f"Earth Engine initialized with project: {PROJECT_ID}")


# ============================================================
# SENTINEL-2 CLOUD MASKING
# ============================================================

def mask_sentinel2_clouds(image):
    """
    Mask clouds and cloud shadows using Sentinel-2 Scene
    Classification Layer (SCL).

    Removed:
        3 = Cloud shadow
        8 = Cloud medium probability
        9 = Cloud high probability
        10 = Thin cirrus
    """

    scl = image.select("SCL")

    mask = (
        scl.neq(3)
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
    )

    return image.updateMask(mask)


# ============================================================
# NDVI CREATION
# ============================================================

def create_ndvi_composite(region):
    """
    Create a median NDVI composite from Sentinel-2 SR Harmonized.
    """

    print("Building Sentinel-2 image collection...")

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                MAX_CLOUD_PERCENTAGE,
            )
        )
        .map(mask_sentinel2_clouds)
    )

    image_count = collection.size().getInfo()

    print(f"Sentinel-2 images found: {image_count}")

    if image_count == 0:
        raise RuntimeError(
            "No Sentinel-2 images found. "
            "Check the date range or cloud threshold."
        )

    print("Calculating NDVI for each image...")

    ndvi_collection = collection.map(
        lambda image: image.normalizedDifference(
            ["B8", "B4"]
        ).rename("ndvi")
    )

    print("Creating temporal median NDVI composite...")

    ndvi = ndvi_collection.median().clip(region)

    return ndvi


# ============================================================
# SAMPLE CONVERSION
# ============================================================

def dataframe_to_feature_collection(df):
    """
    Convert a pandas DataFrame into an Earth Engine FeatureCollection.
    """

    features = []

    for row in df.itertuples(index=False):

        feature = ee.Feature(
            ee.Geometry.Point(
                [
                    float(row.longitude),
                    float(row.latitude),
                ]
            ),
            {
                "sample_id": row.sample_id,
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

def extract_ndvi_batch(ndvi_image, batch_df):
    """
    Extract NDVI values for one batch of sample coordinates.
    """

    points = dataframe_to_feature_collection(batch_df)

    sampled = ndvi_image.sampleRegions(
        collection=points,
        scale=SCALE_METERS,
        geometries=False,
    )

    results = sampled.getInfo()

    rows = []

    for feature in results["features"]:

        properties = feature["properties"]

        rows.append(
            {
                "sample_id": properties["sample_id"],
                "latitude": properties["latitude"],
                "longitude": properties["longitude"],
                "landslide": properties["landslide"],
                "ndvi": properties.get("ndvi"),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    start_time = time.time()

    print("=" * 70)
    print("STEP 34E — SENTINEL-2 NDVI FEATURE EXTRACTION")
    print("=" * 70)

    # --------------------------------------------------------
    # Initialize Earth Engine
    # --------------------------------------------------------

    initialize_earth_engine()

    # --------------------------------------------------------
    # Load samples
    # --------------------------------------------------------

    print("\nLoading ML samples...")

    samples = pd.read_csv(INPUT_FILE)

    required_columns = {
        "sample_id",
        "latitude",
        "longitude",
        "landslide",
    }

    missing_columns = required_columns - set(samples.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print(f"Input samples: {len(samples)}")

    # --------------------------------------------------------
    # Create study region
    # --------------------------------------------------------

    min_lon = samples["longitude"].min()
    max_lon = samples["longitude"].max()

    min_lat = samples["latitude"].min()
    max_lat = samples["latitude"].max()

    region = ee.Geometry.Rectangle(
        [
            float(min_lon),
            float(min_lat),
            float(max_lon),
            float(max_lat),
        ]
    )

    print(
        "\nStudy region bounds:"
    )

    print(
        f"Longitude: {min_lon:.6f} to {max_lon:.6f}"
    )

    print(
        f"Latitude : {min_lat:.6f} to {max_lat:.6f}"
    )

    # --------------------------------------------------------
    # Create NDVI composite
    # --------------------------------------------------------

    ndvi_image = create_ndvi_composite(region)

    # --------------------------------------------------------
    # Extract NDVI in batches
    # --------------------------------------------------------

    print("\nExtracting NDVI values...")

    output_batches = []

    total_batches = (
        len(samples) + BATCH_SIZE - 1
    ) // BATCH_SIZE

    for batch_number, start_index in enumerate(
        range(0, len(samples), BATCH_SIZE),
        start=1,
    ):

        end_index = min(
            start_index + BATCH_SIZE,
            len(samples),
        )

        batch_df = samples.iloc[
            start_index:end_index
        ]

        print(
            f"Processing batch "
            f"{batch_number}/{total_batches} "
            f"({len(batch_df)} samples)..."
        )

        batch_result = extract_ndvi_batch(
            ndvi_image,
            batch_df,
        )

        output_batches.append(batch_result)

        print(
            f"Extracted values: "
            f"{len(batch_result)}"
        )

    # --------------------------------------------------------
    # Combine results
    # --------------------------------------------------------

    # Combine raw EE batch results (may have fewer rows than input
    # if EE dropped masked/no-data pixels — detected below)
    raw_result = pd.concat(
        output_batches,
        ignore_index=True,
    )

    ee_returned = len(raw_result)
    ee_dropped  = len(samples) - ee_returned
    if ee_dropped > 0:
        print(
            f"Note: Earth Engine returned {ee_returned} rows; "
            f"{ee_dropped} sample(s) had fully masked NDVI "
            f"(will be NaN in output)."
        )

    # --------------------------------------------------------
    # Merge back onto original input to preserve all 11,046 rows
    # Missing EE rows become NaN in the ndvi column (not dropped)
    # --------------------------------------------------------

    result = (
        samples[
            [
                "sample_id",
                "latitude",
                "longitude",
                "landslide",
            ]
        ]
        .merge(
            raw_result[["sample_id", "ndvi"]],
            on="sample_id",
            how="left",
        )
    )

    # --------------------------------------------------------
    # VALIDATION  (run after merge so all 11,046 rows present)
    # --------------------------------------------------------

    print("\nRunning validation...")

    if len(result) != len(samples):
        raise ValueError(
            f"Row count mismatch after merge: "
            f"expected {len(samples)}, "
            f"got {len(result)}"
        )

    if result["sample_id"].nunique() != len(samples):
        raise ValueError(
            "Duplicate or missing sample IDs detected."
        )

    if result["sample_id"].duplicated().sum() != 0:
        raise ValueError(
            "Duplicate sample IDs detected."
        )

    expected_ids = set(samples["sample_id"])
    actual_ids   = set(result["sample_id"])
    missing_ids  = expected_ids - actual_ids
    if missing_ids:
        raise ValueError(
            f"Missing sample IDs in output: {len(missing_ids)}"
        )

    unexpected_ids = actual_ids - expected_ids
    if unexpected_ids:
        raise ValueError(
            f"Unexpected sample IDs in output: {len(unexpected_ids)}"
        )

    if not set(result["landslide"].unique()).issubset({0, 1}):
        raise ValueError("Invalid landslide labels detected.")

    pos_count = int((result["landslide"] == 1).sum())
    neg_count = int((result["landslide"] == 0).sum())
    if pos_count != 5523 or neg_count != 5523:
        raise ValueError(
            f"Class balance altered: pos={pos_count}, neg={neg_count}"
        )

    # Check for infinite NDVI values
    import numpy as np
    ndvi_arr  = result["ndvi"].values.astype(float)
    inf_pos   = int(np.isposinf(ndvi_arr).sum())
    inf_neg   = int(np.isneginf(ndvi_arr).sum())
    if inf_pos + inf_neg > 0:
        raise ValueError(
            f"+/-Inf NDVI values found: +inf={inf_pos}, -inf={inf_neg}"
        )

    print("All validation checks PASSED.")

    # --------------------------------------------------------
    # Save output
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("STEP 34E COMPLETED")
    print("=" * 70)

    print(f"Output file: {OUTPUT_FILE}")

    print(f"Output rows: {len(result)}")

    print(
        f"Unique sample IDs: "
        f"{result['sample_id'].nunique()}"
    )

    print(
        f"Duplicate sample IDs: "
        f"{result['sample_id'].duplicated().sum()}"
    )

    ndvi_valid = result["ndvi"].dropna()

    print(f"Missing NDVI values:  {result['ndvi'].isna().sum()}")
    print(f"+Inf NDVI count:      {inf_pos}")
    print(f"-Inf NDVI count:      {inf_neg}")
    print(f"NDVI minimum:         {ndvi_valid.min():.6f}")
    print(f"NDVI maximum:         {ndvi_valid.max():.6f}")
    print(f"NDVI mean:            {ndvi_valid.mean():.6f}")
    print(f"NDVI median:          {ndvi_valid.median():.6f}")
    print(f"NDVI std dev:         {ndvi_valid.std():.6f}")
    print(f"Positive samples:     {pos_count:,}")
    print(f"Negative samples:     {neg_count:,}")
    print(f"Class balance:        {'OK' if pos_count==5523 and neg_count==5523 else 'ERROR'}")
    print(f"Labels preserved:     YES")
    print(f"Input CSV modified:   NO")
    print(f"Execution time:       {elapsed:.2f} seconds")
    print()
    print(">>> No machine learning model training was performed during Step 34E. <<<")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()