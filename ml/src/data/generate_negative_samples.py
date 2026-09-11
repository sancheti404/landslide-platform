"""
Negative Sample Generation Pipeline for Uttarakhand Landslide Susceptibility Modeling

SCIENTIFIC DOCUMENTATION & METHODOLOGY:

1. WHY NEGATIVE SAMPLES ARE REQUIRED:
   Supervised machine learning models (e.g. Random Forest, XGBoost, Neural Networks) for
   landslide susceptibility modeling require binary classification targets (Landslide = 1 vs. Non-Landslide = 0).
   Since historical inventory databases (e.g. GSI Bhusanket) only record positive landslide occurrences (landslide = 1),
   pseudo-negative (background) samples must be generated to represent non-landslide conditions across the landscape.

2. WHY ARBITRARY RANDOM POINTS CANNOT AUTOMATICALLY BE CALLED SAFE:
   Landslide inventory mapping is often incomplete due to remote mountainous terrain, cloud cover in optical imagery,
   or unmapped historical events. Sampling arbitrary random points across the study area without spatial constraints
   risks labeling unmapped or active landslide locations as "safe" (false negatives), introducing severe label noise
   into machine learning training.

3. WHY EXCLUSION BUFFERING IS USED:
   To minimize label contamination, spatial exclusion buffering (here, 2,000 meters) is applied around every known
   positive landslide point. This ensures candidate negative points are drawn outside the spatial footprint, local slope
   corridor, and immediate spatial autocorrelation zone of historical landslides.

4. WHY A PROJECTED CRS IS REQUIRED FOR METER-BASED DISTANCE CALCULATIONS:
   Geographic coordinate systems (EPSG:4326 - WGS84) express coordinates in angular degrees (latitude/longitude).
   Because longitudinal degree length contracts towards the poles, calculating spatial buffer distances (in meters)
   directly on spherical coordinates produces severe distortion. A projected planar Coordinate Reference System
   tailored to Uttarakhand (UTM Zone 44N - EPSG:32644) is required so that 1 coordinate unit equals exactly 1 meter.

5. SCIENTIFIC LIMITATION (PSEUDO-NEGATIVE SAMPLING):
   These generated samples represent 'pseudo-negative' or 'background' points sampled from valid non-landslide areas,
   rather than ground-truthed, field-verified non-landslide locations. They serve as background spatial controls
   for modeling purposes.
"""

import os
import sys
import logging
import urllib.request
import zipfile
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep
from shapely.strtree import STRtree

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
RANDOM_SEED = 42
EXCLUSION_DISTANCE_METERS = 2000.0
PROJECTED_CRS = "EPSG:32644"  # WGS 84 / UTM zone 44N (Uttarakhand / Northern India)
GEOGRAPHIC_CRS = "EPSG:4326"  # WGS 84 Geographic Coordinates

def find_positive_csv():
    """Locate the cleaned positive landslide inventory CSV file."""
    candidate_paths = [
        os.path.join("ml", "data", "processed", "uttarakhand_landslide_inventory_clean.csv"),
        os.path.join("data", "processed", "uttarakhand_landslide_inventory_clean.csv"),
        "uttarakhand_landslide_inventory_clean.csv"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            logger.info(f"Found positive inventory CSV at: {path}")
            return path
    raise FileNotFoundError("Could not locate uttarakhand_landslide_inventory_clean.csv file.")

def load_or_acquire_uttarakhand_boundary():
    """
    Load or automatically download the official GeoBoundaries Uttarakhand administrative boundary.
    Dataset: GeoBoundaries IND ADM1 (v4.0 / gbOpen)
    Source: GeoBoundaries (William & Mary geoLab - https://www.geoboundaries.org/)
    """
    external_dir = os.path.join("ml", "data", "external")
    os.makedirs(external_dir, exist_ok=True)
    
    extracted_dir = os.path.join(external_dir, "geoBoundaries_IND_ADM1")
    geojson_path = os.path.join(extracted_dir, "geoBoundaries-IND-ADM1.geojson")
    simplified_path = os.path.join(external_dir, "geoBoundaries-IND-ADM1_simplified.geojson")

    if os.path.exists(geojson_path):
        logger.info(f"Loading existing administrative boundary from: {geojson_path}")
        boundary_path = geojson_path
    elif os.path.exists(simplified_path):
        logger.info(f"Loading existing administrative boundary from: {simplified_path}")
        boundary_path = simplified_path
    else:
        logger.info("Boundary file not found locally. Downloading official GeoBoundaries IND ADM1 dataset...")
        zip_url = "https://github.com/wmgeolab/geoBoundaries/raw/ac277e29ad1ac188822f81c88c9215cb67598575/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1-all.zip"
        zip_dest = os.path.join(external_dir, "geoBoundaries-IND-ADM1-all.zip")
        
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(zip_dest, 'wb') as out:
            out.write(resp.read())
            
        logger.info(f"Downloaded boundary zip archive ({os.path.getsize(zip_dest)} bytes). Extracting...")
        with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
            zip_ref.extractall(extracted_dir)
            
        boundary_path = geojson_path
        logger.info(f"Boundary extracted successfully to: {boundary_path}")

    # Read boundary shape using GeoPandas
    gdf_boundary = gpd.read_file(boundary_path)
    uk_gdf = gdf_boundary[gdf_boundary['shapeName'].str.lower().str.contains('uttarakhand', na=False)]
    
    if uk_gdf.empty:
        raise ValueError("Could not find Uttarakhand polygon in boundary dataset.")
        
    logger.info(f"Successfully loaded Uttarakhand boundary polygon ({len(uk_gdf)} feature). Source CRS: {uk_gdf.crs}")
    return uk_gdf, boundary_path

def generate_negative_samples():
    """Execute reproducible negative sample generation workflow."""
    logger.info("Starting Negative Sample Generation Pipeline...")
    
    # 1. Load Positive Landslide Data
    pos_csv = find_positive_csv()
    pos_df = pd.read_csv(pos_csv)
    n_positives = len(pos_df)
    n_requested_negatives = n_positives
    logger.info(f"Loaded {n_positives} positive landslide inventory points.")

    # Convert positive points to GeoDataFrame (EPSG:4326 -> EPSG:32644)
    pos_gdf_4326 = gpd.GeoDataFrame(
        pos_df,
        geometry=gpd.points_from_xy(pos_df['longitude'], pos_df['latitude']),
        crs=GEOGRAPHIC_CRS
    )
    pos_gdf_proj = pos_gdf_4326.to_crs(PROJECTED_CRS)
    pos_geoms = pos_gdf_proj.geometry.values
    pos_tree = STRtree(pos_geoms)

    # 2. Load Uttarakhand Administrative Boundary
    uk_gdf_4326, boundary_path = load_or_acquire_uttarakhand_boundary()
    uk_gdf_proj = uk_gdf_4326.to_crs(PROJECTED_CRS)
    uk_poly_proj = uk_gdf_proj.geometry.union_all()
    prep_uk_poly_proj = prep(uk_poly_proj)

    # 3. Create Spatial Exclusion Buffer around Positive Points
    logger.info(f"Creating {EXCLUSION_DISTANCE_METERS:.0f}-meter spatial exclusion buffer around positive points in {PROJECTED_CRS}...")
    pos_buffers = pos_gdf_proj.geometry.buffer(EXCLUSION_DISTANCE_METERS, resolution=32)
    pos_buffer_union = pos_buffers.union_all()

    # Valid sampling area = Uttarakhand Polygon - Positive Buffer Union
    valid_sampling_area = uk_poly_proj.difference(pos_buffer_union)
    prep_valid_area = prep(valid_sampling_area)

    # 4. Uniform Random Sampling with Fixed Seed 42
    logger.info(f"Sampling candidate negative points (Target count: {n_requested_negatives}, Seed: {RANDOM_SEED})...")
    rng = np.random.default_rng(RANDOM_SEED)

    minx, miny, maxx, maxy = valid_sampling_area.bounds
    candidates_generated = 0
    candidates_rejected = 0
    valid_neg_points_proj = []

    batch_size = n_requested_negatives * 2

    while len(valid_neg_points_proj) < n_requested_negatives:
        xs = rng.uniform(minx, maxx, batch_size)
        ys = rng.uniform(miny, maxy, batch_size)
        candidates_generated += batch_size

        for x, y in zip(xs, ys):
            p = Point(x, y)
            # Check 1: Inside valid sampling polygon
            if prep_valid_area.contains(p):
                # Check 2: Explicit distance check to nearest positive point
                nearest_idx = pos_tree.nearest(p)
                dist = p.distance(pos_geoms[nearest_idx])
                if dist >= EXCLUSION_DISTANCE_METERS:
                    valid_neg_points_proj.append(p)
                    if len(valid_neg_points_proj) == n_requested_negatives:
                        break
                else:
                    candidates_rejected += 1
            else:
                candidates_rejected += 1

    generated_count = len(valid_neg_points_proj)
    if generated_count < n_requested_negatives:
        raise RuntimeError(f"Failed to generate requested {n_requested_negatives} negative samples. Generated only {generated_count}.")

    logger.info(f"Sampling complete. Generated {generated_count} valid negative samples. Rejected {candidates_rejected} candidates.")

    # 5. Project Negative Samples back to EPSG:4326
    neg_gdf_proj = gpd.GeoDataFrame(geometry=valid_neg_points_proj, crs=PROJECTED_CRS)
    neg_gdf_4326 = neg_gdf_proj.to_crs(GEOGRAPHIC_CRS)

    # 6. Spatial Distance & Validity Verification
    logger.info("Performing comprehensive spatial validation checks...")
    neg_proj_geoms = neg_gdf_proj.geometry.values
    nearest_indices = pos_tree.nearest(neg_proj_geoms)
    nearest_pos_geoms = pos_geoms[nearest_indices]
    distances = np.array([neg.distance(pos) for neg, pos in zip(neg_proj_geoms, nearest_pos_geoms)])

    min_dist = float(distances.min())
    mean_dist = float(distances.mean())
    max_dist = float(distances.max())

    samples_inside_buffer = int((distances < EXCLUSION_DISTANCE_METERS).sum())
    
    # Boundary validation in projected CRS
    samples_outside_boundary = sum(not prep_uk_poly_proj.contains(p) for p in neg_proj_geoms)

    # Coordinate duplicate validation
    coords_4326 = [(round(p.x, 8), round(p.y, 8)) for p in neg_gdf_4326.geometry]
    duplicate_coord_count = len(coords_4326) - len(set(coords_4326))

    if min_dist < EXCLUSION_DISTANCE_METERS - 1e-5:
        raise ValueError(f"Validation Failure: Minimum distance ({min_dist:.2f}m) is less than exclusion distance ({EXCLUSION_DISTANCE_METERS}m).")
    if samples_outside_boundary > 0:
        raise ValueError(f"Validation Failure: Found {samples_outside_boundary} negative samples outside Uttarakhand boundary.")
    if duplicate_coord_count > 0:
        raise ValueError(f"Validation Failure: Found {duplicate_coord_count} duplicate negative coordinates.")

    logger.info("All spatial validation checks PASSED successfully.")

    # 7. Construct Output Dataframe
    output_records = []
    for i, p in enumerate(neg_gdf_4326.geometry, 1):
        output_records.append({
            "sample_id": f"UK_NEG_{i:05d}",
            "latitude": p.y,
            "longitude": p.x,
            "landslide": 0
        })

    df_neg_output = pd.DataFrame(output_records)

    # 8. Save Output CSV
    output_dir = os.path.join("ml", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "uttarakhand_negative_samples.csv")
    df_neg_output.to_csv(output_csv, index=False)
    logger.info(f"Saved generated negative samples to: {output_csv}")

    # 9. Print Concise Final Report
    print("\n" + "=" * 60)
    print("CONCISE FINAL REPORT: NEGATIVE SAMPLE GENERATION")
    print("=" * 60)
    print(f"Boundary Dataset Source: GeoBoundaries IND ADM1 (v4.0 / gbOpen)")
    print(f"Boundary File Used: {boundary_path}")
    print(f"Projected CRS Used: {PROJECTED_CRS} (WGS 84 / UTM zone 44N)")
    print(f"Positive Points Count: {n_positives}")
    print(f"Exclusion Distance: {EXCLUSION_DISTANCE_METERS:.0f} meters")
    print(f"Requested Negative Count: {n_requested_negatives}")
    print(f"Generated Negative Count: {generated_count}")
    print(f"Rejected Candidates Count: {candidates_rejected}")
    print("-" * 60)
    print("Nearest Positive Distance Metrics:")
    print(f"  Minimum Distance: {min_dist:.4f} meters")
    print(f"  Mean Distance:    {mean_dist:.4f} meters")
    print(f"  Maximum Distance: {max_dist:.4f} meters")
    print("-" * 60)
    print(f"Samples Outside Uttarakhand Boundary: {samples_outside_boundary}")
    print(f"Samples Inside {EXCLUSION_DISTANCE_METERS:.0f}m Buffer: {samples_inside_buffer}")
    print(f"Duplicate Negative Coordinates: {duplicate_coord_count}")
    print(f"Latitude Range:  [{df_neg_output['latitude'].min():.6f}, {df_neg_output['latitude'].max():.6f}]")
    print(f"Longitude Range: [{df_neg_output['longitude'].min():.6f}, {df_neg_output['longitude'].max():.6f}]")
    print("-" * 60)
    print(f"Output Dataset Path: {output_csv}")
    print(f"Output Dataset Columns: {list(df_neg_output.columns)}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    generate_negative_samples()
