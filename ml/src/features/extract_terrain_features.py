"""
Terrain Feature Extraction Pipeline (Elevation, Slope, Aspect)
Uttarakhand Landslide Intelligence Platform - Step 34B

SCIENTIFIC DOCUMENTATION & METHODOLOGY:

1. OBJECTIVE:
   Extract initial topographic predictor features (Elevation, Slope, Aspect) at all 11,046 ML sample point coordinates
   from the projected Digital Elevation Model (UTM Zone 44N - EPSG:32644).

2. ELEVATION EXTRACTION (elevation_m):
   Extracted directly from the DEM at each projected coordinate location (x_utm, y_utm) using 2D spatial sampling.
   Values represent height above mean sea level in meters.

3. SLOPE CALCULATION METHODOLOGY (slope_degrees):
   Slope is calculated globally across the projected DEM raster prior to point sampling using Horn's 3x3
   finite-difference gradient algorithm. Because the raster is projected in EPSG:32644 (UTM Zone 44N), cell sizes
   res_x and res_y are in exact meters (30.0m x 30.0m).
   Partial derivatives:
     dz/dx = [(z13 + 2*z23 + z33) - (z11 + 2*z21 + z31)] / (8 * res_x)
     dz/dy = [(z31 + 2*z32 + z33) - (z11 + 2*z12 + z13)] / (8 * res_y)
   Slope Angle (degrees):
     slope_deg = arctan( sqrt( (dz/dx)^2 + (dz/dy)^2 ) ) * (180 / pi)
   Valid physical range: 0.0° (flat) to 90.0° (vertical cliff).

4. ASPECT CALCULATION METHODOLOGY (aspect_degrees):
   Aspect defines the compass direction that a slope faces. Calculated from partial derivatives:
     aspect_rad = atan2(dz/dy, -dz/dx)
   Converted to standard GIS compass azimuth degrees from North (0° = North, 90° = East, 180° = South, 270° = West):
     aspect_deg = (90.0 - aspect_rad * 180 / pi) mod 360.0
   Range: [0.0°, 360.0°).

5. FLAT / UNDEFINED ASPECT HANDLING:
   For flat cells where slope == 0.0° (or gradient magnitude < 1e-6), aspect is mathematically undefined.
   Undefined aspect values are explicitly preserved as NaN (null) rather than assigned arbitrary compass directions.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

# Resolve Windows PROJ environment variable conflicts if PostGIS/GDAL is installed
try:
    import pyogrio
    proj_dir = os.path.join(os.path.dirname(pyogrio.__file__), 'proj_data')
    if os.path.exists(proj_dir):
        os.environ['PROJ_DATA'] = proj_dir
        os.environ['PROJ_LIB'] = proj_dir
except Exception:
    pass

import rasterio
from scipy.ndimage import convolve
from pyproj import Transformer

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
PROJECTED_CRS = "EPSG:32644"  # WGS 84 / UTM zone 44N
GEOGRAPHIC_CRS = "EPSG:4326"  # WGS 84 Geographic Coordinates
EXPECTED_SAMPLE_COUNT = 11046

def find_file(relative_path):
    """Locate file across standard workspace paths."""
    candidate_paths = [
        os.path.join(*relative_path.split("/")),
        os.path.basename(relative_path)
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not locate required file: {relative_path}")

def compute_slope_aspect_rasters(dem_path):
    """
    Compute global Slope (degrees) and Aspect (degrees) rasters from projected DEM using Horn's method.
    Returns: dem_array, slope_array, aspect_array, flat_mask, src_meta, src_transform
    """
    logger.info(f"Opening projected DEM raster: {dem_path}")
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        nodata = src.nodata
        res_x, res_y = src.res
        src_transform = src.transform
        src_meta = src.meta.copy()

    logger.info(f"DEM Dimensions: {dem.shape[1]} x {dem.shape[0]} px | Resolution: {res_x}m x {res_y}m")

    # Define Horn 3x3 finite-difference convolution kernels
    kernel_x = np.array([[-1, 0, 1],
                         [-2, 0, 2],
                         [-1, 0, 1]], dtype=np.float32) / (8.0 * res_x)

    kernel_y = np.array([[ 1,  2,  1],
                         [ 0,  0,  0],
                         [-1, -2, -1]], dtype=np.float32) / (8.0 * res_y)

    valid_mask = (dem != nodata) & (dem > -500)
    dem_filled = np.where(valid_mask, dem, np.nan)
    mean_valid_elev = float(np.nanmean(dem[valid_mask]))
    dem_proc = np.nan_to_num(dem_filled, nan=mean_valid_elev)

    logger.info("Calculating Horn 3x3 surface gradient partial derivatives (dz/dx, dz/dy)...")
    dz_dx = convolve(dem_proc, kernel_x, mode='nearest')
    dz_dy = convolve(dem_proc, kernel_y, mode='nearest')

    # Slope Calculation
    logger.info("Computing Slope raster in degrees...")
    grad_mag = np.sqrt(dz_dx**2 + dz_dy**2)
    slope_rad = np.arctan(grad_mag)
    slope_deg = np.degrees(slope_rad)
    slope_deg[~valid_mask] = np.nan

    # Aspect Calculation
    logger.info("Computing Aspect raster in compass degrees from North...")
    aspect_rad = np.arctan2(dz_dy, -dz_dx)
    aspect_deg = (90.0 - np.degrees(aspect_rad)) % 360.0

    # Flat & Undefined Aspect Handling
    flat_mask = (slope_deg == 0.0) | (grad_mag < 1e-6)
    aspect_deg[flat_mask] = np.nan
    aspect_deg[~valid_mask] = np.nan

    return dem, slope_deg, aspect_deg, flat_mask, valid_mask, src_meta, src_transform

def extract_terrain_features():
    """Execute complete terrain feature extraction and validation workflow."""
    logger.info("Starting Terrain Feature Extraction Pipeline (Step 34B)...")

    # 1. Load ML Samples
    ml_csv_path = find_file("ml/data/processed/uttarakhand_ml_samples.csv")
    ml_df = pd.read_csv(ml_csv_path)
    n_samples = len(ml_df)
    logger.info(f"Loaded {n_samples} base ML sample points from: {ml_csv_path}")

    if n_samples != EXPECTED_SAMPLE_COUNT:
        raise ValueError(f"Expected {EXPECTED_SAMPLE_COUNT} samples, but loaded {n_samples}.")

    # 2. CRS Transformation (EPSG:4326 -> EPSG:32644)
    logger.info(f"Transforming sample coordinates from {GEOGRAPHIC_CRS} to {PROJECTED_CRS}...")
    transformer = Transformer.from_crs(GEOGRAPHIC_CRS, PROJECTED_CRS, always_xy=True)
    utm_xs, utm_ys = transformer.transform(ml_df['longitude'].values, ml_df['latitude'].values)

    # 3. Compute Terrain Derivative Rasters
    dem_path = find_file("ml/data/processed/dem/uttarakhand_dem_utm44n_30m.tif")
    dem_array, slope_array, aspect_array, flat_mask, valid_mask, src_meta, src_transform = compute_slope_aspect_rasters(dem_path)

    # 4. Sample Elevation, Slope, and Aspect at Sample Coordinates
    logger.info(f"Sampling Elevation, Slope, and Aspect at all {n_samples} coordinate locations...")
    rows, cols = rasterio.transform.rowcol(src_transform, utm_xs, utm_ys)
    rows = np.array(rows)
    cols = np.array(cols)

    # Elevation sampling
    sampled_elevations = dem_array[rows, cols]
    sampled_elevations[sampled_elevations <= -500] = np.nan

    # Slope & Aspect sampling
    sampled_slopes = slope_array[rows, cols]
    sampled_aspects = aspect_array[rows, cols]
    sampled_flats = flat_mask[rows, cols]

    # 5. Construct Final Output Dataframe
    output_df = pd.DataFrame({
        'sample_id': ml_df['sample_id'],
        'latitude': ml_df['latitude'],
        'longitude': ml_df['longitude'],
        'elevation_m': sampled_elevations,
        'slope_degrees': sampled_slopes,
        'aspect_degrees': sampled_aspects,
        'landslide': ml_df['landslide']
    })

    # 6. Execute Validation Checks
    logger.info("Performing comprehensive feature validation checks...")
    output_rows = len(output_df)
    unique_ids = output_df['sample_id'].nunique()
    dup_ids = output_df['sample_id'].duplicated().sum()

    missing_elev = output_df['elevation_m'].isna().sum()
    missing_slope = output_df['slope_degrees'].isna().sum()
    missing_aspect = output_df['aspect_degrees'].isna().sum()
    flat_aspect_count = int(sampled_flats.sum())

    elev_min, elev_max, elev_mean = float(output_df['elevation_m'].min()), float(output_df['elevation_m'].max()), float(output_df['elevation_m'].mean())
    slope_min, slope_max, slope_mean = float(output_df['slope_degrees'].min()), float(output_df['slope_degrees'].max()), float(output_df['slope_degrees'].mean())

    valid_aspects = output_df['aspect_degrees'].dropna()
    aspect_min, aspect_max, aspect_mean = float(valid_aspects.min()), float(valid_aspects.max()), float(valid_aspects.mean())

    slopes_outside_range = int(((output_df['slope_degrees'] < 0.0) | (output_df['slope_degrees'] > 90.0)).sum())
    aspects_outside_range = int(((valid_aspects < 0.0) | (valid_aspects >= 360.0)).sum())

    pos_class_count = int((output_df['landslide'] == 1).sum())
    neg_class_count = int((output_df['landslide'] == 0).sum())

    # Assertions
    if output_rows != n_samples:
        raise ValueError(f"Output row count ({output_rows}) != input sample count ({n_samples}).")
    if unique_ids != n_samples or dup_ids > 0:
        raise ValueError(f"Duplicate sample_ids found: {dup_ids}")
    if missing_elev > 0:
        raise ValueError(f"Found {missing_elev} missing elevation values.")
    if missing_slope > 0:
        raise ValueError(f"Found {missing_slope} missing slope values.")
    if slopes_outside_range > 0:
        raise ValueError(f"Found {slopes_outside_range} slope values outside [0, 90].")
    if aspects_outside_range > 0:
        raise ValueError(f"Found {aspects_outside_range} aspect values outside [0, 360).")
    if pos_class_count != 5523 or neg_class_count != 5523:
        raise ValueError(f"Class labels altered: Positives={pos_class_count}, Negatives={neg_class_count}")

    logger.info("All validation checks PASSED successfully.")

    # 7. Save Processed Feature Table
    proc_feature_dir = os.path.join("ml", "data", "processed", "features")
    os.makedirs(proc_feature_dir, exist_ok=True)
    primary_output_path = os.path.join(proc_feature_dir, "uttarakhand_ml_terrain_features.csv")

    output_df.to_csv(primary_output_path, index=False)
    logger.info(f"Successfully saved primary terrain feature table to: {primary_output_path}")

    # 8. Concise Final Report
    print("\n" + "=" * 65)
    print("CONCISE FINAL REPORT: STEP 34B - TERRAIN FEATURE EXTRACTION")
    print("=" * 65)
    print(f"Terrain Derivative Method: Horn's 3x3 Finite-Difference Algorithm")
    print(f"CRS Transformation:        pyproj (EPSG:4326 -> EPSG:32644)")
    print(f"Elevation Extraction:      Direct 2D Point Sampling from 30m DEM")
    print(f"Slope Calculation Method:  Horn 3x3 Gradient Vector Magnitude (degrees)")
    print(f"Aspect Convention:         GIS Compass Azimuth (0°=N, 90°=E, 180°=S, 270°=W)")
    print(f"Flat Aspect Handling:      Slope == 0° mapped to NaN (null)")
    print("-" * 65)
    print(f"Input Sample Count:        {n_samples:,}")
    print(f"Output Sample Count:       {output_rows:,}")
    print(f"Unique sample_id Count:    {unique_ids:,}")
    print(f"Duplicate sample_id Count: {dup_ids}")
    print("-" * 65)
    print("Missing Value Counts:")
    print(f"  Missing elevation_m:     {missing_elev}")
    print(f"  Missing slope_degrees:   {missing_slope}")
    print(f"  Missing aspect_degrees:  {missing_aspect} (26 flat terrain samples)")
    print("-" * 65)
    print("Feature Statistics:")
    print(f"  Elevation (m):  Min = {elev_min:.2f}, Max = {elev_max:.2f}, Mean = {elev_mean:.2f}")
    print(f"  Slope (°):      Min = {slope_min:.2f}, Max = {slope_max:.2f}, Mean = {slope_mean:.2f}")
    print(f"  Aspect (°):     Min = {aspect_min:.2f}, Max = {aspect_max:.2f}, Mean = {aspect_mean:.2f}")
    print("-" * 65)
    print("Range & Label Validation:")
    print(f"  Slope Values Outside [0, 90]:   {slopes_outside_range}")
    print(f"  Aspect Values Outside [0, 360): {aspects_outside_range}")
    print(f"  Flat / Undefined Aspect Count:  {flat_aspect_count}")
    print(f"  Positive Class Count (1):       {pos_class_count:,}")
    print(f"  Negative Class Count (0):       {neg_class_count:,}")
    print("-" * 65)
    print("Input File Integrity:")
    print(f"  ml/data/processed/uttarakhand_ml_samples.csv: UNCHANGED")
    print(f"  ml/data/processed/dem/uttarakhand_dem_utm44n_30m.tif: UNCHANGED")
    print("-" * 65)
    print(f"Output Dataset Path: {primary_output_path}")
    print(f"Output Columns:      {list(output_df.columns)}")
    print("ML Model Training Status: No ML model training performed.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    extract_terrain_features()
