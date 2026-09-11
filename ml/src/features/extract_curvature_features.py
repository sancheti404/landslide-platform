"""
Terrain Curvature Feature Extraction Pipeline (Profile & Plan Curvature)
Uttarakhand Landslide Intelligence Platform - Step 34C

================================================================================
SCIENTIFIC DOCUMENTATION & METHODOLOGY
================================================================================

1. OBJECTIVE:
   Derive Profile Curvature and Plan Curvature rasters from the projected 30m SRTM
   DEM (EPSG:32644, UTM Zone 44N) and sample values at all 11,046 ML sample
   coordinate locations using a raster-first workflow. No ML model is trained.

2. RASTER-FIRST WORKFLOW:
   Projected DEM
         |
         v
   First-order derivatives (Horn 3x3 finite-difference, metric units)
         |
         v
   Second-order derivatives (finite-difference, metric units)
         |
         +----------------------------------+
         v                                  v
   Profile Curvature Raster           Plan Curvature Raster
         |                                  |
         +-----------------+-----------------+
                           v
              Point sampling at 11,046 ML coordinates

3. FIRST-ORDER DERIVATIVES (Horn 3x3 Weighted Finite-Difference):
   Using the standard Horn (1981) algorithm on the 3x3 neighbourhood centred at
   each pixel (i, j).

   Neighbourhood labelling (z11...z33):
       z11  z12  z13
       z21  z22  z23
       z31  z32  z33

   Convolution kernels applied at every interior pixel:
       dz/dx  ~= [(z13 + 2*z23 + z33) - (z11 + 2*z21 + z31)] / (8 * res_x)
       dz/dy  ~= [(z31 + 2*z32 + z33) - (z11 + 2*z12 + z13)] / (8 * res_y)

   where res_x = res_y = 30.0 m (UTM Zone 44N projected resolution).

4. SECOND-ORDER DERIVATIVES (Central Finite-Difference):
   d2z/dx2  ~= (z[i, j-1] - 2*z[i, j] + z[i, j+1]) / (res_x^2)
   d2z/dy2  ~= (z[i-1, j] - 2*z[i, j] + z[i+1, j]) / (res_y^2)
   d2z/dxdy ~= (z[i-1, j+1] - z[i-1, j-1] - z[i+1, j+1] + z[i+1, j-1]) / (4 * res_x * res_y)

5. PROFILE CURVATURE (Evans 1979 / Zevenbergen & Thorne 1987):
   profile_curv = -(d2z/dx2*(dz/dx)^2 + 2*d2z/dxdy*(dz/dx)*(dz/dy) + d2z/dy2*(dz/dy)^2)
                   / (p * sqrt(1 + p))
   where p = (dz/dx)^2 + (dz/dy)^2

   SIGN: Negative = upwardly concave (accelerating flow);
         Positive = upwardly convex  (decelerating flow).

6. PLAN CURVATURE (Evans 1979 / Zevenbergen & Thorne 1987):
   plan_curv = -(d2z/dx2*(dz/dy)^2 - 2*d2z/dxdy*(dz/dx)*(dz/dy) + d2z/dy2*(dz/dx)^2)
                / (p * sqrt(p))

   SIGN: Negative = concave in plan (convergent flow);
         Positive = convex in plan  (divergent flow).

7. FLAT / NEAR-ZERO SLOPE HANDLING:
   FLAT_TOLERANCE = 1e-6  (gradient threshold, m/m)
   Condition: p = |grad_z|^2 < FLAT_TOLERANCE^2
   Action: set profile_curvature = NaN, plan_curvature = NaN (explicit NaN, not 0).

8. NUMERICAL STABILITY:
   Any remaining +/-Inf values after division are replaced with NaN and reported.

9. COORDINATE TRANSFORMATION:
   pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)

REFERENCES:
    Horn, B.K.P. (1981). Proc. IEEE, 69(1), 14-47.
    Evans, I.S. (1979). PhD thesis, Univ. Durham.
    Zevenbergen, L.W. & Thorne, C.R. (1987). Earth Surface Processes and Landforms, 12(1), 47-56.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd

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
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECTED_CRS    = "EPSG:32644"  # WGS 84 / UTM Zone 44N
GEOGRAPHIC_CRS   = "EPSG:4326"   # WGS 84 Geographic Coordinates
EXPECTED_SAMPLES = 11_046
FLAT_TOLERANCE   = 1e-6          # |grad z| threshold below which curvature is NaN


def find_file(relative_path: str) -> str:
    """Locate a required file by searching standard workspace paths."""
    candidates = [
        os.path.join(*relative_path.split("/")),
        os.path.basename(relative_path),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        f"Required input file not found: {relative_path}\n"
        "Please run earlier pipeline steps before executing Step 34C."
    )


def _safe_stats(arr: np.ndarray, label: str) -> dict:
    """Compute summary statistics on a 1-D array; report NaN/Inf counts."""
    finite = arr[np.isfinite(arr)]
    stats = {
        "missing": int(np.isnan(arr).sum()),
        "inf_pos": int(np.isposinf(arr).sum()),
        "inf_neg": int(np.isneginf(arr).sum()),
        "min":     float(np.nanmin(finite)) if finite.size > 0 else float("nan"),
        "max":     float(np.nanmax(finite)) if finite.size > 0 else float("nan"),
        "mean":    float(np.nanmean(finite)) if finite.size > 0 else float("nan"),
        "median":  float(np.nanmedian(finite)) if finite.size > 0 else float("nan"),
        "std":     float(np.nanstd(finite)) if finite.size > 0 else float("nan"),
    }
    logger.info(
        f"{label} - missing: {stats['missing']}, +inf: {stats['inf_pos']}, "
        f"-inf: {stats['inf_neg']}, min: {stats['min']:.6f}, "
        f"max: {stats['max']:.6f}, mean: {stats['mean']:.6f}, "
        f"median: {stats['median']:.6f}, std: {stats['std']:.6f}"
    )
    return stats


def compute_curvature_rasters(dem_path: str):
    """
    Derive Profile Curvature and Plan Curvature rasters from the projected DEM.

    Returns
    -------
    profile_curv : np.ndarray  shape = dem.shape, dtype float32
    plan_curv    : np.ndarray  shape = dem.shape, dtype float32
    src_transform: rasterio.Affine
    flat_count   : int - number of near-flat pixels set to NaN
    inf_count    : int - number of inf pixels replaced with NaN
    """
    logger.info(f"Opening projected DEM: {dem_path}")
    with rasterio.open(dem_path) as src:
        dem           = src.read(1).astype(np.float64)   # float64 for numerical precision
        nodata        = src.nodata
        res_x, res_y  = src.res                           # metres (UTM)
        src_transform = src.transform
        logger.info(
            f"DEM shape: {dem.shape[1]}x{dem.shape[0]} px | "
            f"Resolution: {res_x:.2f}m x {res_y:.2f}m | "
            f"CRS: {src.crs}"
        )

    # Mask no-data cells and fill with mean elevation for convolution
    valid_mask = np.ones(dem.shape, dtype=bool)
    if nodata is not None:
        valid_mask &= (dem != nodata)
    valid_mask &= (dem > -500)

    mean_elev  = float(np.mean(dem[valid_mask]))
    dem_filled = np.where(valid_mask, dem, mean_elev)  # fill for convolve

    # ---- Step A: First-order derivatives (Horn 3x3) -------------------------
    logger.info("Computing first-order derivatives dz/dx and dz/dy (Horn 3x3)...")

    kernel_x = np.array([[-1, 0, 1],
                          [-2, 0, 2],
                          [-1, 0, 1]], dtype=np.float64) / (8.0 * res_x)

    # raster row axis increases south; kernel_y reflects north-positive dz/dy
    kernel_y = np.array([[ 1,  2,  1],
                          [ 0,  0,  0],
                          [-1, -2, -1]], dtype=np.float64) / (8.0 * res_y)

    dz_dx = convolve(dem_filled, kernel_x, mode='nearest')   # dz/dx
    dz_dy = convolve(dem_filled, kernel_y, mode='nearest')   # dz/dy

    # ---- Step B: Second-order derivatives (central finite-difference) --------
    logger.info("Computing second-order derivatives d2z/dx2, d2z/dy2, d2z/dxdy...")

    # Pad DEM to avoid edge artefacts on 1-pixel borders
    dem_pad = np.pad(dem_filled, 1, mode='edge')

    # d2z/dx2 = (z[i, j-1] - 2*z[i, j] + z[i, j+1]) / res_x^2
    d2z_dx2 = (dem_pad[1:-1, :-2] - 2.0 * dem_pad[1:-1, 1:-1] + dem_pad[1:-1, 2:]) / (res_x ** 2)

    # d2z/dy2 = (z[i-1, j] - 2*z[i, j] + z[i+1, j]) / res_y^2
    d2z_dy2 = (dem_pad[:-2, 1:-1] - 2.0 * dem_pad[1:-1, 1:-1] + dem_pad[2:, 1:-1]) / (res_y ** 2)

    # d2z/dxdy = (z[i-1,j+1] - z[i-1,j-1] - z[i+1,j+1] + z[i+1,j-1]) / (4*res_x*res_y)
    d2z_dxdy = (
        dem_pad[:-2, 2:] - dem_pad[:-2, :-2]
        - dem_pad[2:, 2:] + dem_pad[2:, :-2]
    ) / (4.0 * res_x * res_y)

    # ---- Step C: Gradient magnitude squared p = |grad_z|^2 ------------------
    p = dz_dx ** 2 + dz_dy ** 2

    flat_mask  = p < (FLAT_TOLERANCE ** 2)
    flat_count = int(flat_mask.sum())
    logger.info(f"Near-flat pixels (|grad_z| < {FLAT_TOLERANCE}): {flat_count:,}")

    p_safe      = np.where(flat_mask, np.nan, p)
    sqrt_p_safe = np.sqrt(p_safe)

    # ---- Step D: Profile Curvature ------------------------------------------
    logger.info("Computing Profile Curvature raster...")
    numerator_prof = -(
        d2z_dx2 * dz_dx ** 2
        + 2.0 * d2z_dxdy * dz_dx * dz_dy
        + d2z_dy2 * dz_dy ** 2
    )
    denominator_prof = p_safe * np.sqrt(1.0 + p_safe)

    with np.errstate(invalid='ignore', divide='ignore'):
        profile_curv = np.where(flat_mask, np.nan, numerator_prof / denominator_prof)

    # ---- Step E: Plan Curvature ---------------------------------------------
    logger.info("Computing Plan Curvature raster...")
    numerator_plan = -(
        d2z_dx2 * dz_dy ** 2
        - 2.0 * d2z_dxdy * dz_dx * dz_dy
        + d2z_dy2 * dz_dx ** 2
    )
    denominator_plan = p_safe * sqrt_p_safe   # p^(3/2)

    with np.errstate(invalid='ignore', divide='ignore'):
        plan_curv = np.where(flat_mask, np.nan, numerator_plan / denominator_plan)

    # ---- Step F: Mask no-data cells -----------------------------------------
    profile_curv[~valid_mask] = np.nan
    plan_curv[~valid_mask]    = np.nan

    # ---- Step G: Replace remaining +/-Inf with NaN --------------------------
    inf_prof  = int(np.isinf(profile_curv).sum())
    inf_plan  = int(np.isinf(plan_curv).sum())
    inf_count = inf_prof + inf_plan
    if inf_count > 0:
        logger.warning(
            f"Replacing {inf_count} infinite curvature values with NaN "
            f"({inf_prof} profile, {inf_plan} plan)."
        )
    profile_curv[np.isinf(profile_curv)] = np.nan
    plan_curv[np.isinf(plan_curv)]       = np.nan

    # Cast to float32 for memory efficiency
    profile_curv = profile_curv.astype(np.float32)
    plan_curv    = plan_curv.astype(np.float32)

    return profile_curv, plan_curv, src_transform, flat_count, inf_count


def extract_curvature_features() -> None:
    """Execute the complete Step 34C curvature feature extraction pipeline."""
    logger.info("=" * 70)
    logger.info("Starting Step 34C - Terrain Curvature Feature Extraction")
    logger.info("=" * 70)

    # ---- 1. Verify and load input files ------------------------------------
    ml_csv_path = find_file("ml/data/processed/uttarakhand_ml_samples.csv")
    dem_path    = find_file("ml/data/processed/dem/uttarakhand_dem_utm44n_30m.tif")

    # Record file sizes before processing (integrity check)
    ml_size_before  = os.path.getsize(ml_csv_path)
    dem_size_before = os.path.getsize(dem_path)

    logger.info(f"Input ML samples: {ml_csv_path}")
    logger.info(f"Input DEM:        {dem_path}")

    ml_df   = pd.read_csv(ml_csv_path)
    n_input = len(ml_df)
    logger.info(f"Loaded {n_input:,} ML sample rows.")

    if n_input != EXPECTED_SAMPLES:
        raise ValueError(
            f"Expected {EXPECTED_SAMPLES} samples, found {n_input}. "
            "Ensure all earlier pipeline steps completed successfully."
        )

    required_cols = {"sample_id", "latitude", "longitude", "landslide"}
    missing_cols  = required_cols - set(ml_df.columns)
    if missing_cols:
        raise ValueError(f"ML samples CSV missing columns: {missing_cols}")

    # ---- 2. CRS transformation: EPSG:4326 -> EPSG:32644 -------------------
    logger.info(f"Transforming coordinates from {GEOGRAPHIC_CRS} to {PROJECTED_CRS}...")
    transformer = Transformer.from_crs(GEOGRAPHIC_CRS, PROJECTED_CRS, always_xy=True)
    utm_xs, utm_ys = transformer.transform(
        ml_df['longitude'].values,
        ml_df['latitude'].values
    )

    # ---- 3. Compute curvature rasters ------------------------------------
    profile_raster, plan_raster, src_transform, flat_pix_count, inf_replaced = \
        compute_curvature_rasters(dem_path)

    # ---- 4. Sample curvature rasters at all ML coordinates ----------------
    logger.info(f"Sampling curvature rasters at {n_input:,} coordinate locations...")
    rows_idx, cols_idx = rasterio.transform.rowcol(src_transform, utm_xs, utm_ys)
    rows_idx = np.asarray(rows_idx, dtype=np.intp)
    cols_idx = np.asarray(cols_idx, dtype=np.intp)

    h, w = profile_raster.shape

    # Detect out-of-bounds coordinates
    out_of_bounds = (
        (rows_idx < 0) | (rows_idx >= h) |
        (cols_idx < 0) | (cols_idx >= w)
    )
    n_oob = int(out_of_bounds.sum())
    if n_oob > 0:
        logger.warning(
            f"{n_oob} sample coordinates projected outside DEM extent - "
            "setting to NaN."
        )

    rows_safe = np.clip(rows_idx, 0, h - 1)
    cols_safe = np.clip(cols_idx, 0, w - 1)

    sampled_profile = profile_raster[rows_safe, cols_safe].astype(np.float64)
    sampled_plan    = plan_raster[rows_safe, cols_safe].astype(np.float64)

    # Set OOB samples to NaN
    sampled_profile[out_of_bounds] = np.nan
    sampled_plan[out_of_bounds]    = np.nan

    # Final safety: replace any +/-Inf in sampled arrays
    inf_s_prof = int(np.isinf(sampled_profile).sum())
    inf_s_plan = int(np.isinf(sampled_plan).sum())
    if (inf_s_prof + inf_s_plan) > 0:
        logger.warning(
            f"Replacing {inf_s_prof + inf_s_plan} infinite values in sampled "
            "arrays with NaN."
        )
    sampled_profile[np.isinf(sampled_profile)] = np.nan
    sampled_plan[np.isinf(sampled_plan)]        = np.nan

    # ---- 5. Build output DataFrame ----------------------------------------
    output_df = pd.DataFrame({
        'sample_id':         ml_df['sample_id'].values,
        'latitude':          ml_df['latitude'].values,
        'longitude':         ml_df['longitude'].values,
        'profile_curvature': sampled_profile,
        'plan_curvature':    sampled_plan,
        'landslide':         ml_df['landslide'].values,
    })

    n_output = len(output_df)
    if n_output != n_input:
        raise ValueError(
            f"Row count mismatch: input={n_input}, output={n_output}. "
            "No rows should be dropped."
        )

    # ---- 6. Validation ----------------------------------------------------
    logger.info("Performing comprehensive output validation...")

    unique_ids = output_df['sample_id'].nunique()
    dup_ids    = int(output_df['sample_id'].duplicated().sum())

    prof_arr   = output_df['profile_curvature'].values.astype(np.float64)
    plan_arr   = output_df['plan_curvature'].values.astype(np.float64)

    prof_stats = _safe_stats(prof_arr, "Profile Curvature")
    plan_stats = _safe_stats(plan_arr, "Plan Curvature")

    pos_count = int((output_df['landslide'] == 1).sum())
    neg_count = int((output_df['landslide'] == 0).sum())

    # Sample-ID integrity
    original_ids  = set(ml_df['sample_id'].values)
    output_ids    = set(output_df['sample_id'].values)
    ids_preserved = (original_ids == output_ids)

    # Label integrity
    labels_preserved = np.array_equal(
        ml_df['landslide'].values,
        output_df['landslide'].values
    )

    # Input file size integrity
    ml_size_after  = os.path.getsize(ml_csv_path)
    dem_size_after = os.path.getsize(dem_path)
    ml_unchanged   = (ml_size_before == ml_size_after)
    dem_unchanged  = (dem_size_before == dem_size_after)

    # Assertions
    if dup_ids > 0:
        raise ValueError(f"Duplicate sample_id values found: {dup_ids}")
    if not ids_preserved:
        raise ValueError("sample_id set mismatch between input and output!")
    if not labels_preserved:
        raise ValueError("Landslide labels altered between input and output!")
    if not ml_unchanged:
        raise RuntimeError("Input ML samples CSV has been modified (size changed)!")
    if not dem_unchanged:
        raise RuntimeError("Input DEM has been modified (size changed)!")

    logger.info("All validation checks PASSED.")

    # ---- 7. Save output CSV -----------------------------------------------
    out_dir  = os.path.join("ml", "data", "processed", "features")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "uttarakhand_ml_curvature_features.csv")
    output_df.to_csv(out_path, index=False)
    logger.info(f"Saved curvature feature table -> {out_path}")

    # ---- 8. Final Report --------------------------------------------------
    sep  = "=" * 70
    dash = "-" * 70

    print(f"\n{sep}")
    print("FINAL REPORT - STEP 34C: TERRAIN CURVATURE FEATURE EXTRACTION")
    print(sep)
    print("Files Created:")
    print("  Script:  ml/src/features/extract_curvature_features.py")
    print(f"  Output:  {out_path}")
    print(dash)
    print("DEM & Pixel Resolution:")
    print("  CRS:        EPSG:32644 (WGS 84 / UTM Zone 44N)")
    print("  Resolution: 30.0 m x 30.0 m")
    print(f"  Source:     {dem_path}")
    print(dash)
    print("Terrain Derivative Methodology:")
    print("  Workflow:     Raster-first (global raster derivatives, then point sampling)")
    print("  First-order:  Horn (1981) 3x3 weighted finite-difference (metric units)")
    print("    dz/dx ~= [(z13+2z23+z33)-(z11+2z21+z31)] / (8*res_x)")
    print("    dz/dy ~= [(z31+2z32+z33)-(z11+2z12+z13)] / (8*res_y)")
    print("  Second-order: Central finite-difference (res_x=res_y=30 m)")
    print("    d2z/dx2  ~= (z[i,j-1] - 2z[i,j] + z[i,j+1]) / (30^2)")
    print("    d2z/dy2  ~= (z[i-1,j] - 2z[i,j] + z[i+1,j]) / (30^2)")
    print("    d2z/dxdy ~= (z[i-1,j+1]-z[i-1,j-1]-z[i+1,j+1]+z[i+1,j-1]) / (4*30*30)")
    print(dash)
    print("Profile Curvature:")
    print("  Formula: -(d2z/dx2*px^2 + 2*d2z/dxdy*px*py + d2z/dy2*py^2) / (p*sqrt(1+p))")
    print("  Sign (+): Upwardly convex (decelerating downslope flow)")
    print("  Sign (-): Upwardly concave (accelerating downslope flow)")
    print("  Convention: Esri / Evans (1979) / Zevenbergen & Thorne (1987)")
    print(dash)
    print("Plan Curvature:")
    print("  Formula: -(d2z/dx2*py^2 - 2*d2z/dxdy*px*py + d2z/dy2*px^2) / (p*sqrt(p))")
    print("  Sign (+): Convex in plan (divergent lateral flow)")
    print("  Sign (-): Concave in plan (convergent lateral flow)")
    print("  Convention: Esri / Evans (1979) / Zevenbergen & Thorne (1987)")
    print(dash)
    print("Flat / Near-Zero Slope Handling:")
    print(f"  Tolerance:   FLAT_TOLERANCE = {FLAT_TOLERANCE} (|grad_z| threshold, m/m)")
    print(f"  Condition:   p = |grad_z|^2 < {FLAT_TOLERANCE**2:.2e}")
    print("  Action:      Set profile_curvature = NaN, plan_curvature = NaN")
    print(f"  Pixel count: {flat_pix_count:,} near-flat DEM pixels identified")
    print(dash)
    print("Row Counts:")
    print(f"  Input samples:        {n_input:,}")
    print(f"  Output rows:          {n_output:,}")
    print(f"  Unique sample_id:     {unique_ids:,}")
    print(f"  Duplicate sample_id:  {dup_ids}")
    print(f"  Out-of-bounds coords: {n_oob}")
    print(dash)
    print("Profile Curvature Statistics:")
    print(f"  Missing (NaN):   {prof_stats['missing']}")
    print(f"  Min:             {prof_stats['min']:.6f}")
    print(f"  Max:             {prof_stats['max']:.6f}")
    print(f"  Mean:            {prof_stats['mean']:.6f}")
    print(f"  Median:          {prof_stats['median']:.6f}")
    print(f"  Std Dev:         {prof_stats['std']:.6f}")
    print(f"  +Inf count:      {prof_stats['inf_pos']}")
    print(f"  -Inf count:      {prof_stats['inf_neg']}")
    print(dash)
    print("Plan Curvature Statistics:")
    print(f"  Missing (NaN):   {plan_stats['missing']}")
    print(f"  Min:             {plan_stats['min']:.6f}")
    print(f"  Max:             {plan_stats['max']:.6f}")
    print(f"  Mean:            {plan_stats['mean']:.6f}")
    print(f"  Median:          {plan_stats['median']:.6f}")
    print(f"  Std Dev:         {plan_stats['std']:.6f}")
    print(f"  +Inf count:      {plan_stats['inf_pos']}")
    print(f"  -Inf count:      {plan_stats['inf_neg']}")
    print(dash)
    print("Infinite Value Validation (raster-wide, before sampling):")
    print(f"  Total +/-Inf replaced in curvature rasters: {inf_replaced}")
    print(dash)
    print("Class Label Integrity:")
    print(f"  Positive samples (landslide=1): {pos_count:,}")
    print(f"  Negative samples (landslide=0): {neg_count:,}")
    print(f"  Labels preserved:               {'YES' if labels_preserved else 'NO - ERROR'}")
    print(dash)
    print("Sample ID Integrity:")
    print(f"  All sample_ids preserved:       {'YES' if ids_preserved else 'NO - ERROR'}")
    print(dash)
    print("Input File Integrity (size-based check):")
    print(f"  uttarakhand_ml_samples.csv:     {'UNCHANGED' if ml_unchanged else 'MODIFIED - ERROR'}")
    print(f"  uttarakhand_dem_utm44n_30m.tif: {'UNCHANGED' if dem_unchanged else 'MODIFIED - ERROR'}")
    print(sep)
    print()
    print(">>> No machine learning model training was performed during Step 34C. <<<")
    print(sep + "\n")


if __name__ == "__main__":
    extract_curvature_features()
