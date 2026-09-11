"""
Base ML Sample Dataset Builder for Uttarakhand Landslide Susceptibility Modeling

SCIENTIFIC & PIPELINE DOCUMENTATION:

1. WHY POSITIVES AND PSEUDO-NEGATIVES ARE COMBINED:
   Machine learning algorithms (such as Random Forest, Gradient Boosting, and Neural Networks)
   require a balanced binary training dataset containing both target presence (Landslide = 1)
   and background presence/absence (Landslide = 0) locations. Combining validated positive inventory
   events with spatially constrained pseudo-negative samples creates the unified spatial base sample
   table required for feature extraction.

2. WHY THIS DATASET IS NOT YET READY FOR TRAINING:
   At this stage, the base ML sample dataset contains only spatial point coordinates (latitude, longitude)
   and binary class labels (landslide). Machine learning models cannot be trained directly on raw geographic
   coordinates alone without risking spatial overfitting. Environmental predictors (covariates) such as:
     - Topographic factors: Elevation, Slope, Aspect, Plan/Profile Curvature, TPI, TRI
     - Geological factors: Lithology, Distance to Faults
     - Hydrological factors: Topographic Wetness Index (TWI), Distance to Streams
     - Environmental factors: NDVI, Land Cover / Land Use
     - Meteorological factors: Annual Mean & Extreme Precipitation
   must be spatially extracted and appended at each coordinate location before model training can begin.

3. PSEUDO-NEGATIVE / BACKGROUND LABELING LIMITATION:
   Pseudo-negative samples (landslide = 0) represent background spatial locations sampled from valid areas
   at least 2,000 meters away from any known historical landslide point. They represent background environmental
   conditions across Uttarakhand rather than field-verified stable terrain.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_STATE = 42
EXPECTED_POSITIVE_COUNT = 5523
EXPECTED_NEGATIVE_COUNT = 5523
EXPECTED_TOTAL_COUNT = EXPECTED_POSITIVE_COUNT + EXPECTED_NEGATIVE_COUNT

def find_input_file(filename):
    """Locate input CSV file across standard candidate paths."""
    candidate_paths = [
        os.path.join("ml", "data", "processed", filename),
        os.path.join("data", "processed", filename),
        filename
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            logger.info(f"Found input file '{filename}' at: {path}")
            return path
    raise FileNotFoundError(f"Could not locate required input file: {filename}")

def build_base_ml_dataset():
    """Build and validate the unified base ML sample dataset."""
    logger.info("Starting Base ML Sample Dataset Builder...")

    # 1. Locate and Load Input Datasets
    pos_path = find_input_file("uttarakhand_landslide_inventory_clean.csv")
    neg_path = find_input_file("uttarakhand_negative_samples.csv")

    pos_raw_df = pd.read_csv(pos_path)
    neg_raw_df = pd.read_csv(neg_path)

    n_pos_raw = len(pos_raw_df)
    n_neg_raw = len(neg_raw_df)

    logger.info(f"Loaded positive dataset: {n_pos_raw} rows.")
    logger.info(f"Loaded negative dataset: {n_neg_raw} rows.")

    # Validate Input Row Counts
    if n_pos_raw != EXPECTED_POSITIVE_COUNT:
        raise ValueError(f"Expected {EXPECTED_POSITIVE_COUNT} positive samples, but found {n_pos_raw}.")
    if n_neg_raw != EXPECTED_NEGATIVE_COUNT:
        raise ValueError(f"Expected {EXPECTED_NEGATIVE_COUNT} negative samples, but found {n_neg_raw}.")

    # 2. Format Positive Samples
    # Generate deterministic sample_id: POS_000001, POS_000002, ..., POS_005523
    pos_samples = pd.DataFrame({
        'sample_id': [f"POS_{i:06d}" for i in range(1, n_pos_raw + 1)],
        'latitude': pos_raw_df['latitude'].astype(float),
        'longitude': pos_raw_df['longitude'].astype(float),
        'landslide': 1
    })

    # 3. Format Negative Samples
    neg_samples = pd.DataFrame({
        'sample_id': neg_raw_df['sample_id'].astype(str),
        'latitude': neg_raw_df['latitude'].astype(float),
        'longitude': neg_raw_df['longitude'].astype(float),
        'landslide': 0
    })

    # 4. Combine Datasets
    combined_df = pd.concat([pos_samples, neg_samples], ignore_index=True)

    # 5. Shuffle Deterministically (random_state = 42)
    logger.info(f"Shuffling combined dataset deterministically with random_state={RANDOM_STATE}...")
    shuffled_df = combined_df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)

    # 6. Comprehensive Dataset Validation
    logger.info("Executing comprehensive validation checks on base ML sample dataset...")

    total_rows = len(shuffled_df)
    pos_count = int((shuffled_df['landslide'] == 1).sum())
    neg_count = int((shuffled_df['landslide'] == 0).sum())

    duplicate_sample_ids = int(shuffled_df['sample_id'].duplicated().sum())
    duplicate_rows = int(shuffled_df.duplicated().sum())
    missing_coords = int((shuffled_df['latitude'].isna() | shuffled_df['longitude'].isna()).sum())
    
    invalid_lat = int(((shuffled_df['latitude'] < -90.0) | (shuffled_df['latitude'] > 90.0)).sum())
    invalid_lon = int(((shuffled_df['longitude'] < -180.0) | (shuffled_df['longitude'] > 180.0)).sum())
    invalid_labels = int((~shuffled_df['landslide'].isin([0, 1])).sum())

    lat_min, lat_max = float(shuffled_df['latitude'].min()), float(shuffled_df['latitude'].max())
    lon_min, lon_max = float(shuffled_df['longitude'].min()), float(shuffled_df['longitude'].max())

    # Assertions
    if total_rows != EXPECTED_TOTAL_COUNT:
        raise ValueError(f"Validation Failure: Total rows ({total_rows}) != {EXPECTED_TOTAL_COUNT}")
    if pos_count != EXPECTED_POSITIVE_COUNT:
        raise ValueError(f"Validation Failure: Positive count ({pos_count}) != {EXPECTED_POSITIVE_COUNT}")
    if neg_count != EXPECTED_NEGATIVE_COUNT:
        raise ValueError(f"Validation Failure: Negative count ({neg_count}) != {EXPECTED_NEGATIVE_COUNT}")
    if duplicate_sample_ids > 0:
        raise ValueError(f"Validation Failure: Found {duplicate_sample_ids} duplicate sample_ids.")
    if duplicate_rows > 0:
        raise ValueError(f"Validation Failure: Found {duplicate_rows} exact duplicate rows.")
    if missing_coords > 0:
        raise ValueError(f"Validation Failure: Found {missing_coords} missing coordinate values.")
    if invalid_lat > 0 or invalid_lon > 0:
        raise ValueError(f"Validation Failure: Found invalid geographic coordinates (Lat: {invalid_lat}, Lon: {invalid_lon}).")
    if invalid_labels > 0:
        raise ValueError(f"Validation Failure: Found invalid landslide labels ({invalid_labels}).")

    logger.info("All validation checks PASSED successfully.")

    # 7. Save Output CSV
    output_dir = os.path.join("ml", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "uttarakhand_ml_samples.csv")

    shuffled_df.to_csv(output_csv, index=False)
    logger.info(f"Successfully saved base ML dataset to: {output_csv}")

    # 8. Print Concise Final Report
    print("\n" + "=" * 60)
    print("CONCISE FINAL REPORT: BASE ML SAMPLE DATASET BUILD")
    print("=" * 60)
    print(f"Positive Input File:  {pos_path} ({n_pos_raw} rows)")
    print(f"Negative Input File:  {neg_path} ({n_neg_raw} rows)")
    print("-" * 60)
    print(f"Input Row Counts:      Positives = {n_pos_raw}, Negatives = {n_neg_raw}")
    print(f"Output Total Row Count: {total_rows}")
    print(f"Positive Class Count (landslide = 1): {pos_count}")
    print(f"Negative Class Count (landslide = 0): {neg_count}")
    print("-" * 60)
    print(f"Final Column Names:   {list(shuffled_df.columns)}")
    print(f"Duplicate sample_id Count: {duplicate_sample_ids}")
    print(f"Duplicate Complete Row Count: {duplicate_rows}")
    print(f"Missing Coordinate Count:   {missing_coords}")
    print(f"Latitude Range:  [{lat_min:.6f}, {lat_max:.6f}]")
    print(f"Longitude Range: [{lon_min:.6f}, {lon_max:.6f}]")
    print("-" * 60)
    print(f"Deterministic Shuffle Seed: random_state = {RANDOM_STATE}")
    print(f"ML Training Status: No ML model training performed.")
    print(f"Output Dataset Path: {output_csv}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    build_base_ml_dataset()
