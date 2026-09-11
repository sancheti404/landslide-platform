"""
Acquire and Validate Digital Elevation Model (DEM) Pipeline
Uttarakhand Landslide Intelligence Platform - Step 34A

SCIENTIFIC & TECHNICAL DOCUMENTATION:

1. DEM PRODUCT IDENTIFICATION & RESOLUTION:
   Product: Shuttle Radar Topography Mission (SRTM) GL1 Global 30m DEM (1 arc-second).
   Spatial Resolution: ~30 meters (0.00027777778 decimal degrees per pixel; 30.0m x 30.0m in UTM Zone 44N).

2. SCIENTIFIC CLASSIFICATION (DSM vs. DTM):
   CRITICAL SCIENTIFIC DISTINCTION:
   SRTM elevation data was acquired in February 2000 using C-band interferometric synthetic aperture radar (InSAR).
   Because C-band radar signals reflect off vegetation canopy, forest foliage, and built structures, SRTM scientifically
   represents a Digital Surface Model (DSM) or canopy-top elevation model, rather than a bare-earth LiDAR Digital
   Terrain Model (DTM). In dense Himalayan forest vegetation (such as Garhwal and Kumaon forest ranges), SRTM values
   include canopy height additions (~10-30m above ground level).

3. COORDINATE REFERENCE SYSTEM & PROJECTED TRANSFORM:
   Raw Global DEMs are distributed in geographic coordinates (EPSG:4326 - WGS84 degrees).
   Calculating horizontal distance-dependent terrain derivatives (such as slope angle in degrees, aspect, plan/profile
   curvature, and Topographic Wetness Index) directly on degree-based spatial grids is mathematically invalid because
   1 degree of longitude varies with latitude (from ~104 km at 28°N to ~98 km at 32°N).
   Therefore, the study-area DEM is reprojected to UTM Zone 44N (EPSG:32644), a conformal planar projected CRS
   where coordinates are in exact horizontal meters (1 unit = 1 meter).

4. STUDY AREA CLIPPING & MARGIN STRATEGY:
   To prevent boundary edge truncation artifacts during 3x3 moving window terrain derivative calculations (Step 34B),
   the study-area DEM is clipped using a 0.20° (~20 km) geographic margin buffer beyond the Uttarakhand administrative
   boundary and ML sample bounding box. This guarantees 100% spatial coverage for all 11,046 ML sample points.
"""

import os
import sys
import logging
import gzip
import requests
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from concurrent.futures import ThreadPoolExecutor

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
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

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
EXPECTED_ML_SAMPLES_COUNT = 11046
MARGIN_DEGREES = 0.20  # ~20km geographic margin for derivative calculations

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

def download_srtm_tile(args):
    """Download single 1x1 degree SRTM GL1 tile from public open repository or OpenTopography."""
    lat, lon, tiles_dir, session = args
    tile_name = f"N{lat:02d}E{lon:03d}"
    gz_path = os.path.join(tiles_dir, f"{tile_name}.hgt.gz")
    hgt_path = os.path.join(tiles_dir, f"{tile_name}.hgt")

    if os.path.exists(hgt_path) and os.path.getsize(hgt_path) > 10000000:
        return hgt_path

    url = f"https://elevation-tiles-prod.s3.amazonaws.com/skadi/N{lat:02d}/{tile_name}.hgt.gz"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for attempt in range(3):
        try:
            r = session.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                with open(gz_path, 'wb') as f_out:
                    f_out.write(r.content)
                with gzip.open(gz_path, 'rb') as f_in, open(hgt_path, 'wb') as f_out:
                    f_out.write(f_in.read())
                if os.path.exists(gz_path):
                    os.remove(gz_path)
                logger.info(f"Downloaded SRTM GL1 tile: {tile_name}")
                return hgt_path
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for tile {tile_name}: {e}")

    return None

def acquire_dem_tiles(min_lon, min_lat, max_lon, max_lat):
    """Acquire all required 1x1 degree SRTM GL1 tiles covering the study area."""
    tiles_dir = os.path.join("ml", "data", "external", "dem", "srtm_tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    lat_start = int(np.floor(min_lat))
    lat_end = int(np.floor(max_lat)) + 1
    lon_start = int(np.floor(min_lon))
    lon_end = int(np.floor(max_lon)) + 1

    tile_grid = []
    for lat in range(lat_start, lat_end):
        for lon in range(lon_start, lon_end):
            tile_grid.append((lat, lon, tiles_dir, requests.Session()))

    logger.info(f"Acquiring {len(tile_grid)} SRTM GL1 30m 1°x1° tiles covering Uttarakhand grid (Lat: {lat_start}-{lat_end-1}, Lon: {lon_start}-{lon_end-1})...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(download_srtm_tile, tile_grid))

    valid_tiles = [r for r in results if r and os.path.exists(r)]
    logger.info(f"Tile acquisition complete. {len(valid_tiles)} / {len(tile_grid)} HGT tiles ready.")

    if len(valid_tiles) < len(tile_grid):
        raise RuntimeError(f"Failed to acquire all required DEM tiles ({len(valid_tiles)} / {len(tile_grid)} downloaded).")

    return valid_tiles

def main():
    logger.info("Starting DEM Acquisition and Validation Pipeline (Step 34A)...")

    # 1. Load ML sample coordinates & Administrative Boundary
    ml_samples_path = find_file("ml/data/processed/uttarakhand_ml_samples.csv")
    ml_df = pd.read_csv(ml_samples_path)
    n_ml_samples = len(ml_df)
    logger.info(f"Loaded {n_ml_samples} ML sample coordinates for validation.")

    boundary_path = find_file("ml/data/external/geoBoundaries_IND_ADM1/geoBoundaries-IND-ADM1.geojson")
    uk_gdf = gpd.read_file(boundary_path)
    uk_poly = uk_gdf[uk_gdf['shapeName'].str.lower().str.contains('uttarakhand', na=False)]

    if uk_poly.empty:
        raise ValueError("Could not locate Uttarakhand boundary polygon.")

    # Determine bounding envelope including ML samples and boundary polygon + margin
    ml_gdf_4326 = gpd.GeoDataFrame(
        ml_df,
        geometry=gpd.points_from_xy(ml_df['longitude'], ml_df['latitude']),
        crs=GEOGRAPHIC_CRS
    )
    
    uk_bounds = uk_poly.total_bounds
    ml_bounds = ml_gdf_4326.total_bounds

    min_lon = min(uk_bounds[0], ml_bounds[0]) - MARGIN_DEGREES
    min_lat = min(uk_bounds[1], ml_bounds[1]) - MARGIN_DEGREES
    max_lon = max(uk_bounds[2], ml_bounds[2]) + MARGIN_DEGREES
    max_lat = max(uk_bounds[3], ml_bounds[3]) + MARGIN_DEGREES

    logger.info(f"Study area spatial bounding envelope with {MARGIN_DEGREES}° margin: Lon [{min_lon:.4f}, {max_lon:.4f}], Lat [{min_lat:.4f}, {max_lat:.4f}]")

    # 2. Acquire Raw DEM Tiles
    hgt_tile_paths = acquire_dem_tiles(min_lon, min_lat, max_lon, max_lat)

    # 3. Merge Raw DEM Tiles into External Raw Raster
    ext_dem_dir = os.path.join("ml", "data", "external", "dem")
    os.makedirs(ext_dem_dir, exist_ok=True)
    raw_dem_path = os.path.join(ext_dem_dir, "uttarakhand_srtm_dem_raw.tif")

    logger.info("Merging raw SRTM GL1 tiles into seamless GeoTIFF raster...")
    src_files = [rasterio.open(f) for f in hgt_tile_paths]
    mosaic, out_trans = merge(src_files)

    raw_meta = src_files[0].meta.copy()
    raw_meta.update({
        'driver': 'GTiff',
        'height': mosaic.shape[1],
        'width': mosaic.shape[2],
        'transform': out_trans,
        'crs': src_files[0].crs,
        'nodata': -32768
    })

    with rasterio.open(raw_dem_path, 'w', **raw_meta) as dest:
        dest.write(mosaic)

    for s in src_files:
        s.close()
        
    logger.info(f"Saved raw merged DEM ({mosaic.shape[2]} x {mosaic.shape[1]} px) to: {raw_dem_path}")

    # 4. Clip DEM to Study Area Envelope with Margin
    proc_dem_dir = os.path.join("ml", "data", "processed", "dem")
    os.makedirs(proc_dem_dir, exist_ok=True)
    clipped_wgs84_path = os.path.join(proc_dem_dir, "uttarakhand_dem_wgs84_30m.tif")

    logger.info(f"Clipping study-area DEM with {MARGIN_DEGREES}° margin...")
    study_envelope = box(min_lon, min_lat, max_lon, max_lat)
    env_gdf = gpd.GeoDataFrame(geometry=[study_envelope], crs=GEOGRAPHIC_CRS)

    with rasterio.open(raw_dem_path) as src:
        out_img, out_transform = mask(src, env_gdf.geometry, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            'driver': 'GTiff',
            'height': out_img.shape[1],
            'width': out_img.shape[2],
            'transform': out_transform
        })
        with rasterio.open(clipped_wgs84_path, 'w', **out_meta) as dest:
            dest.write(out_img)

    logger.info(f"Saved clipped study-area DEM (WGS84) to: {clipped_wgs84_path}")

    # 5. Reproject DEM to Projected CRS (UTM Zone 44N - EPSG:32644) at 30m resolution
    projected_path = os.path.join(proc_dem_dir, "uttarakhand_dem_utm44n_30m.tif")
    logger.info(f"Reprojecting study-area DEM to {PROJECTED_CRS} (UTM Zone 44N) at exact 30m resolution...")

    with rasterio.open(clipped_wgs84_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, PROJECTED_CRS, src.width, src.height, *src.bounds, resolution=30.0
        )
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': PROJECTED_CRS,
            'transform': transform,
            'width': width,
            'height': height,
            'nodata': -32768
        })

        with rasterio.open(projected_path, 'w', **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=PROJECTED_CRS,
                resampling=Resampling.bilinear
            )

    logger.info(f"Successfully saved projected 30m DEM ({width} x {height} px) to: {projected_path}")

    # 6. Comprehensive DEM Validation & ML Sample Coverage Check
    logger.info("Executing comprehensive validation metrics calculation...")
    with rasterio.open(projected_path) as src:
        band = src.read(1)
        nodata = src.nodata
        valid_mask = (band != nodata) & (band > -500)

        total_pixels = int(band.size)
        valid_pixels = int(valid_mask.sum())
        nodata_pixels = total_pixels - valid_pixels
        nodata_pct = (nodata_pixels / total_pixels) * 100.0

        elev_min = float(band[valid_mask].min())
        elev_max = float(band[valid_mask].max())
        elev_mean = float(band[valid_mask].mean())

        raster_bounds = src.bounds
        num_bands = src.count
        dtype_name = str(src.dtypes[0])

        # Validate spatial coverage for all 11,046 ML sample coordinates
        ml_gdf_proj = ml_gdf_4326.to_crs(PROJECTED_CRS)
        coords = [(geom.x, geom.y) for geom in ml_gdf_proj.geometry]
        sampled_elevs = [e[0] for e in src.sample(coords)]

        uncovered_count = sum(e == nodata or e < -500 for e in sampled_elevs)
        covered_count = n_ml_samples - uncovered_count
        coverage_pct = (covered_count / n_ml_samples) * 100.0

    if uncovered_count > 0:
        raise ValueError(f"Validation Failure: {uncovered_count} ML sample points are not covered by the DEM.")

    logger.info("All DEM validation checks PASSED successfully.")

    # 7. Print Concise Final Report
    print("\n" + "=" * 65)
    print("CONCISE FINAL REPORT: STEP 34A - DEM ACQUISITION & VALIDATION")
    print("=" * 65)
    print(f"DEM Provider / Source: NASA / USGS SRTM GL1 (Open Data S3 Mirror)")
    print(f"Exact Dataset Name:    SRTM GL1 Global 30m (1 Arc-Second) DEM")
    print(f"Acquisition Method:    Automated Multi-threaded HTTP Tile Downloader")
    print(f"API / Env Vars Required: OPENTOPO_API_KEY  (Optional; open mirror used)")
    print("-" * 65)
    print(f"Original Resolution:  ~30 meters (1 arc-second / 0.00027778°)")
    print(f"Projected CRS:        {PROJECTED_CRS} (WGS 84 / UTM Zone 44N)")
    print(f"Raster Dimensions:    {width} width x {height} height pixels ({total_pixels:,} cells)")
    print(f"Raster Bands:         {num_bands} band ({dtype_name})")
    print(f"Raster Bounds (UTM):  [{raster_bounds.left:.2f}, {raster_bounds.bottom:.2f}, {raster_bounds.right:.2f}, {raster_bounds.top:.2f}]")
    print("-" * 65)
    print("Elevation Statistics (Valid Cells):")
    print(f"  Minimum Elevation:  {elev_min:.2f} meters")
    print(f"  Maximum Elevation:  {elev_max:.2f} meters")
    print(f"  Mean Elevation:     {elev_mean:.2f} meters")
    print(f"NoData Cell Count:    {nodata_pixels:,} cells ({nodata_pct:.2f}%)")
    print("-" * 65)
    print(f"ML Samples Coverage:  {covered_count:,} / {n_ml_samples:,} points covered ({coverage_pct:.1f}%)")
    print(f"Uncovered Points:     {uncovered_count}")
    print("-" * 65)
    print("Clipping & Margin Strategy:")
    print(f"  Uttarakhand Boundary + {MARGIN_DEGREES}° Margin Buffer (~20 km)")
    print(f"  Edge Effect Prevention: Margin preserved for Step 34B terrain derivatives")
    print("-" * 65)
    print("Output Raster Paths:")
    print(f"  Raw DEM (External):       {raw_dem_path}")
    print(f"  Clipped DEM (WGS84):      {clipped_wgs84_path}")
    print(f"  Projected DEM (UTM 44N):  {projected_path}")
    print("-" * 65)
    print("Scientific Product Type: Digital Surface Model (DSM - Canopy Top)")
    print("ML Training Status:      No ML model training was performed.")
    print("Feature Extraction:      No feature extraction was performed (Step 34A only).")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
