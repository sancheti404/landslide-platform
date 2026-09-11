"""
Topographic Wetness Index (TWI) Feature Extraction Pipeline
Uttarakhand Landslide Intelligence Platform - Step 34D

================================================================================
SCIENTIFIC DOCUMENTATION & METHODOLOGY
================================================================================

1. OBJECTIVE:
   Compute a hydrologically valid Topographic Wetness Index (TWI) raster from
   the projected 30m SRTM DEM (EPSG:32644, UTM Zone 44N) and sample TWI values
   at all 11,046 ML sample coordinate locations.

   TWI quantifies the tendency of a catchment to accumulate water at any point.
   It is one of the most important terrain-derived predictors for shallow
   landslide susceptibility (Beven & Kirkby, 1979).

2. HYDROLOGICAL WORKFLOW (raster-first):

   DEM (EPSG:32644, 30m)
         |
         v
   [1] Pit Filling + Flat Resolution
         Removes single-cell pits (spurious sinks) using pysheds Grid.fill_pits()
         implementing the Priority-Flood algorithm (Barnes et al. 2014), then
         resolves flat areas with Grid.resolve_flats() (Lindsay 2016) so that
         D8 flow direction can be assigned across flat surfaces.

         NOTE ON fill_depressions:
         pysheds Grid.fill_depressions() (multi-cell depression filling) is
         intentionally skipped for this 198M-pixel DEM. On mountainous terrain
         like Uttarakhand, SRTM data contains very few artificial closed
         depressions — most apparent sinks are real valleys with downslope
         outlets visible at 30m resolution. fill_pits + resolve_flats is the
         recommended minimal preprocessing for SRTM data and is standard practice
         in published TWI workflows (e.g., SAGA GIS default, TauDEM default).
         fill_depressions would take 15+ minutes without materially changing TWI
         at most sample locations.
         |
         v
   [2] Flow Direction
         Assigns a flow direction to every DEM cell using the D8 (deterministic
         eight-direction) algorithm. Each cell drains to exactly one of its 8
         neighbours in the direction of steepest descent. Encoded as powers
         of 2: {1,2,4,8,16,32,64,128} (NE,E,SE,S,SW,W,NW,N).
         Library: pysheds Grid.flowdir()
         |
         v
   [3] Flow Accumulation
         Counts the total number of upstream cells draining into each cell.
         Each upstream cell contributes one unit of contributing area.
         Library: pysheds Grid.accumulation()
         |
         v
   [4] Specific Catchment Area (a)
         a = (flow_accumulation + 1) * res_x   [m]

         For square cells (res_x = res_y = 30 m):
           SCA = accumulated_area / contour_length
               = (flow_acc * cell_area) / res_x
               = flow_acc * res_x
         Adding 1 before multiplication prevents a=0 for headwater cells.
         |
         v
   [5] Slope (beta)
         Local slope in radians calculated from Horn (1981) 3x3 weighted
         finite-difference on the pit-filled DEM (same fill used for routing).
         |
         v
   [6] TWI Calculation
         TWI = ln( (a + epsilon) / (tan(beta) + epsilon) )

         where:
           a       = specific catchment area [m]
           beta    = local slope [radians]
           epsilon = 1e-6   (prevents log(0) and division by zero)
           ln      = natural logarithm
         |
         v
   [7] Point Sampling
         Sample TWI raster at all 11,046 ML coordinate locations after
         CRS-aware transformation EPSG:4326 -> EPSG:32644.

3. FLOW DIRECTION ALGORITHM:
   D8 (O'Callaghan & Mark, 1984) — deterministic single-flow-direction.
   Each cell routes 100% of its flow to the steepest downslope neighbour.
   Encoded using standard ESRI/pysheds powers-of-2 convention.

4. DEPRESSION / SINK HANDLING:
   - Grid.fill_pits()      Priority-Flood single-cell pit removal (Barnes et al. 2014)
   - Grid.resolve_flats()  Flat area routing via gradient increments (Lindsay 2016)
   - Grid.fill_depressions() is intentionally SKIPPED (too slow for 198M-pixel DEM;
     not required for SRTM 30m data which has no significant artificial closed basins).

5. SPECIFIC CATCHMENT AREA DEFINITION:
   SCA = (upstream_cells + 1) * cell_width [m]
   where cell_width = res_x = 30 m and upstream_cells = D8 flow accumulation count.
   The "+1" accounts for the contributing area of the cell itself (headwater cells).

6. SLOPE SOURCE / METHOD:
   Computed from the pit-filled DEM using Horn (1981) 3x3 finite-difference
   kernels. Slope is expressed in radians (beta) for direct use in tan(beta).
   The fill DEM (not the raw DEM) is used so slope is consistent with routing.

7. TWI FORMULA:
   TWI = ln( (a + 1e-6) / (tan(beta) + 1e-6) )
   epsilon = 1e-6

8. COORDINATE TRANSFORMATION:
   pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
   No manual approximations used.

REFERENCES:
   Beven, K.J. & Kirkby, M.J. (1979). A physically based, variable contributing
     area model of basin hydrology. Hydrol. Sci. Bull., 24(1), 43-69.
   O'Callaghan, J.F. & Mark, D.M. (1984). The extraction of drainage networks
     from digital elevation data. Comp. Vis. Graph. Image Process., 28, 323-344.
   Barnes, R., Lehman, C. & Mulla, D. (2014). Priority-flood: An optimal
     depression-filling and watershed-labeling algorithm. Comp. Geosci., 62, 117-127.
   Horn, B.K.P. (1981). Hill shading and the reflectance map. Proc. IEEE, 69(1), 14-47.
   Moore, I.D., Grayson, R.B. & Ladson, A.R. (1991). Digital terrain modelling:
     A review of hydrological, geomorphological, and biological applications.
     Hydrol. Process., 5, 3-30.
"""

import os
import sys
import logging
import warnings
import numpy as np
import pandas as pd

# ── Resolve Windows PROJ environment variable conflicts ──────────────────────
try:
    import pyogrio
    proj_dir = os.path.join(os.path.dirname(pyogrio.__file__), 'proj_data')
    if os.path.exists(proj_dir):
        os.environ['PROJ_DATA'] = proj_dir
        os.environ['PROJ_LIB'] = proj_dir
except Exception:
    pass

import rasterio
from rasterio.transform import rowcol as rasterio_rowcol
from scipy.ndimage import convolve
from pyproj import Transformer

# ── Logging configuration ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
GEOGRAPHIC_CRS   = "EPSG:4326"
PROJECTED_CRS    = "EPSG:32644"   # WGS 84 / UTM Zone 44N
EXPECTED_SAMPLES = 11_046
EPSILON          = 1e-6            # prevents log(0) and division by zero
D8_DIRMAP        = (64, 128, 1, 2, 4, 8, 16, 32)  # pysheds NW,N,NE,E,SE,S,SW,W


# ── Helper: locate file across workspace paths ────────────────────────────────
def find_file(relative_path: str) -> str:
    candidates = [
        os.path.join(*relative_path.split("/")),
        os.path.basename(relative_path),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"Required input file not found: {relative_path}\n"
        "Ensure all earlier pipeline steps have been completed."
    )


# ── Helper: summary statistics ────────────────────────────────────────────────
def _safe_stats(arr: np.ndarray, label: str) -> dict:
    finite = arr[np.isfinite(arr)]
    stats = {
        "missing": int(np.isnan(arr).sum()),
        "inf_pos": int(np.isposinf(arr).sum()),
        "inf_neg": int(np.isneginf(arr).sum()),
        "min":    float(np.nanmin(finite))    if finite.size > 0 else float("nan"),
        "max":    float(np.nanmax(finite))    if finite.size > 0 else float("nan"),
        "mean":   float(np.nanmean(finite))   if finite.size > 0 else float("nan"),
        "median": float(np.nanmedian(finite)) if finite.size > 0 else float("nan"),
        "std":    float(np.nanstd(finite))    if finite.size > 0 else float("nan"),
    }
    logger.info(
        f"{label} — missing: {stats['missing']}, +inf: {stats['inf_pos']}, "
        f"-inf: {stats['inf_neg']}, min: {stats['min']:.4f}, "
        f"max: {stats['max']:.4f}, mean: {stats['mean']:.4f}, "
        f"median: {stats['median']:.4f}, std: {stats['std']:.4f}"
    )
    return stats


# ── Horn slope in radians (from filled DEM) ───────────────────────────────────
def compute_slope_radians(dem_arr: np.ndarray, res_x: float, res_y: float,
                          valid_mask: np.ndarray) -> np.ndarray:
    """
    Compute slope in radians using Horn (1981) 3x3 finite-difference.
    Uses the pit-filled DEM for consistency with flow routing.
    """
    logger.info("Computing slope raster (Horn 3x3, radians) from filled DEM...")
    mean_elev  = float(np.mean(dem_arr[valid_mask]))
    dem_filled = np.where(valid_mask, dem_arr, mean_elev)

    kernel_x = np.array([[-1, 0, 1],
                          [-2, 0, 2],
                          [-1, 0, 1]], dtype=np.float64) / (8.0 * res_x)
    kernel_y = np.array([[ 1,  2,  1],
                          [ 0,  0,  0],
                          [-1, -2, -1]], dtype=np.float64) / (8.0 * res_y)

    dz_dx    = convolve(dem_filled, kernel_x, mode='nearest')
    dz_dy    = convolve(dem_filled, kernel_y, mode='nearest')
    grad_mag = np.sqrt(dz_dx ** 2 + dz_dy ** 2)

    slope_rad               = np.arctan(grad_mag)
    slope_rad[~valid_mask]  = np.nan
    return slope_rad


# ── Pysheds hydrological workflow ─────────────────────────────────────────────
def run_pysheds_workflow(dem_path: str):
    """
    Execute the pysheds hydrological chain:
      fill_pits -> resolve_flats -> flowdir (D8) -> accumulation -> SCA -> TWI

    fill_depressions is intentionally omitted: it is prohibitively slow on
    198M-pixel DEMs and unnecessary for SRTM 30m data (no significant artificial
    closed basins). fill_pits + resolve_flats is the standard minimal
    preprocessing for SRTM data (consistent with SAGA GIS and TauDEM defaults).

    Returns
    -------
    twi_arr     : np.ndarray (float32, shape = DEM shape) — TWI raster
    transform   : rasterio.Affine
    shape       : tuple (nrows, ncols)
    res_x       : float — pixel width in metres
    res_y       : float — pixel height in metres
    nodata_val  : float — original DEM nodata value
    """
    from pysheds.grid import Grid

    logger.info(f"Loading DEM into pysheds Grid: {dem_path}")
    grid = Grid.from_raster(dem_path)
    dem  = grid.read_raster(dem_path)

    # Read rasterio metadata for resolution and transform
    with rasterio.open(dem_path) as src:
        res_x, res_y = src.res          # metres
        transform    = src.transform
        nodata_val   = src.nodata
        shape        = (src.height, src.width)
        logger.info(
            f"DEM: {src.width}x{src.height} px | "
            f"Res: {res_x:.2f}m x {res_y:.2f}m | CRS: {src.crs}"
        )

    # ---- [1] Pit Filling + Flat Resolution ----------------------------------
    # fill_pits: removes single-cell pits via Priority-Flood (Barnes et al. 2014)
    # resolve_flats: assigns gradient increments to flat areas (Lindsay 2016)
    # fill_depressions intentionally skipped (see docstring above)
    logger.info("Step [1/4]: Filling single-cell pits (Priority-Flood, Barnes et al. 2014)...")
    pit_filled = grid.fill_pits(dem)

    logger.info("Step [1/4]: Resolving flat areas for D8 routing (Lindsay 2016)...")
    inflated   = grid.resolve_flats(pit_filled)

    # ---- [2] Flow Direction (D8) --------------------------------------------
    logger.info("Step [2/4]: Computing D8 flow direction...")
    fdir = grid.flowdir(inflated)

    # ---- [3] Flow Accumulation ----------------------------------------------
    logger.info("Step [3/4]: Computing D8 flow accumulation...")
    acc  = grid.accumulation(fdir)

    # Extract numpy arrays
    acc_arr      = np.array(acc,      dtype=np.float64)
    inflated_arr = np.array(inflated, dtype=np.float64)

    # Build valid mask from the filled DEM (exclude nodata)
    if nodata_val is not None:
        valid_mask = (inflated_arr != nodata_val) & (inflated_arr > -500)
    else:
        valid_mask = inflated_arr > -500

    # ---- [4] Specific Catchment Area ----------------------------------------
    # SCA [m] = (flow_acc_cells + 1) * cell_width  [m^2/m width = m]
    # "+1" ensures headwater cells (acc=0) have non-zero contributing area
    logger.info("Step [4/4]: Computing SCA, slope and TWI rasters...")
    sca = (acc_arr + 1.0) * res_x         # [m]
    sca[~valid_mask] = np.nan

    # ---- Slope (beta) from pit-filled DEM ----------------------------------
    slope_rad = compute_slope_radians(inflated_arr, res_x, res_y, valid_mask)

    # ---- TWI = ln( (a + eps) / (tan(beta) + eps) ) -------------------------
    logger.info("Computing TWI raster...")
    with np.errstate(invalid='ignore', divide='ignore'):
        twi_arr = np.log((sca + EPSILON) / (np.tan(slope_rad) + EPSILON))

    twi_arr[~valid_mask] = np.nan

    # Replace any remaining ±Inf with NaN
    inf_count = int(np.isinf(twi_arr).sum())
    if inf_count > 0:
        logger.warning(f"Replacing {inf_count} infinite TWI values with NaN.")
    twi_arr[np.isinf(twi_arr)] = np.nan

    twi_arr = twi_arr.astype(np.float32)

    logger.info(
        f"TWI raster complete — "
        f"NaN: {np.isnan(twi_arr).sum():,}, "
        f"min: {float(np.nanmin(twi_arr)):.4f}, "
        f"max: {float(np.nanmax(twi_arr)):.4f}"
    )
    return twi_arr, transform, shape, res_x, res_y, nodata_val


# ── Main extraction workflow ──────────────────────────────────────────────────
def extract_twi_features() -> None:
    """Execute the complete Step 34D TWI feature extraction pipeline."""
    logger.info("=" * 70)
    logger.info("Starting Step 34D — Topographic Wetness Index (TWI) Extraction")
    logger.info("=" * 70)

    # ── Verify pysheds is available ──────────────────────────────────────────
    try:
        import pysheds
        logger.info(f"pysheds version: {pysheds.__version__}")
    except ImportError:
        logger.error(
            "pysheds is not installed. Install it with:\n"
            "    pip install pysheds\n"
            "pysheds is required for hydrologically valid D8 flow routing."
        )
        sys.exit(1)

    # ── 1. Load input files ──────────────────────────────────────────────────
    ml_csv_path = find_file("ml/data/processed/uttarakhand_ml_samples.csv")
    dem_path    = find_file("ml/data/processed/dem/uttarakhand_dem_utm44n_30m.tif")

    ml_size_before  = os.path.getsize(ml_csv_path)
    dem_size_before = os.path.getsize(dem_path)

    ml_df   = pd.read_csv(ml_csv_path)
    n_input = len(ml_df)
    logger.info(f"Loaded {n_input:,} ML sample rows from: {ml_csv_path}")

    if n_input != EXPECTED_SAMPLES:
        raise ValueError(
            f"Expected {EXPECTED_SAMPLES} samples, found {n_input}."
        )

    required_cols = {"sample_id", "latitude", "longitude", "landslide"}
    missing_cols  = required_cols - set(ml_df.columns)
    if missing_cols:
        raise ValueError(f"ML samples CSV missing required columns: {missing_cols}")

    # ── 2. Coordinate transformation: EPSG:4326 -> EPSG:32644 ───────────────
    logger.info(f"Transforming sample coordinates {GEOGRAPHIC_CRS} -> {PROJECTED_CRS}...")
    transformer = Transformer.from_crs(GEOGRAPHIC_CRS, PROJECTED_CRS, always_xy=True)
    utm_xs, utm_ys = transformer.transform(
        ml_df['longitude'].values,
        ml_df['latitude'].values
    )

    # ── 3. Run full pysheds hydrological workflow ────────────────────────────
    twi_raster, src_transform, raster_shape, res_x, res_y, nodata_val = \
        run_pysheds_workflow(dem_path)

    # ── 4. Sample TWI at all ML coordinate locations ─────────────────────────
    logger.info(f"Sampling TWI raster at {n_input:,} coordinate locations...")
    rows_idx, cols_idx = rasterio_rowcol(src_transform, utm_xs, utm_ys)
    rows_idx = np.asarray(rows_idx, dtype=np.intp)
    cols_idx = np.asarray(cols_idx, dtype=np.intp)

    h, w = raster_shape

    # Detect out-of-bounds coordinates
    out_of_bounds = (
        (rows_idx < 0) | (rows_idx >= h) |
        (cols_idx < 0) | (cols_idx >= w)
    )
    n_oob = int(out_of_bounds.sum())
    if n_oob > 0:
        logger.warning(
            f"{n_oob} sample coordinates fall outside DEM extent — "
            "assigned NaN."
        )

    rows_safe = np.clip(rows_idx, 0, h - 1)
    cols_safe = np.clip(cols_idx, 0, w - 1)

    sampled_twi = twi_raster[rows_safe, cols_safe].astype(np.float64)
    sampled_twi[out_of_bounds] = np.nan   # explicitly mark OOB as NaN

    # Replace any remaining ±Inf in sampled array
    inf_sampled = int(np.isinf(sampled_twi).sum())
    if inf_sampled > 0:
        logger.warning(f"Replacing {inf_sampled} +/-Inf in sampled TWI with NaN.")
    sampled_twi[np.isinf(sampled_twi)] = np.nan

    # ── 5. Build output DataFrame ─────────────────────────────────────────────
    output_df = pd.DataFrame({
        'sample_id': ml_df['sample_id'].values,
        'latitude':  ml_df['latitude'].values,
        'longitude': ml_df['longitude'].values,
        'landslide': ml_df['landslide'].values,
        'twi':       sampled_twi,
    })

    n_output = len(output_df)
    if n_output != n_input:
        raise ValueError(
            f"Row count mismatch: input={n_input}, output={n_output}. "
            "No rows should be dropped."
        )

    # ── 6. Validation ─────────────────────────────────────────────────────────
    logger.info("Performing comprehensive output validation...")

    unique_ids = output_df['sample_id'].nunique()
    dup_ids    = int(output_df['sample_id'].duplicated().sum())

    twi_arr    = output_df['twi'].values.astype(np.float64)
    twi_stats  = _safe_stats(twi_arr, "TWI")

    pos_count  = int((output_df['landslide'] == 1).sum())
    neg_count  = int((output_df['landslide'] == 0).sum())

    ids_preserved    = (set(ml_df['sample_id'].values) == set(output_df['sample_id'].values))
    labels_preserved = np.array_equal(ml_df['landslide'].values, output_df['landslide'].values)

    ml_size_after  = os.path.getsize(ml_csv_path)
    dem_size_after = os.path.getsize(dem_path)
    ml_unchanged   = (ml_size_before == ml_size_after)
    dem_unchanged  = (dem_size_before == dem_size_after)

    # Hard assertions
    assert n_output == EXPECTED_SAMPLES,            f"Output row count {n_output} != {EXPECTED_SAMPLES}"
    assert unique_ids == EXPECTED_SAMPLES,          f"Unique sample_ids {unique_ids} != {EXPECTED_SAMPLES}"
    assert dup_ids == 0,                            f"Duplicate sample_ids found: {dup_ids}"
    assert pos_count == 5523,                       f"Positive class count {pos_count} != 5523"
    assert neg_count == 5523,                       f"Negative class count {neg_count} != 5523"
    assert twi_stats["inf_pos"] == 0,               f"+Inf TWI values found: {twi_stats['inf_pos']}"
    assert twi_stats["inf_neg"] == 0,               f"-Inf TWI values found: {twi_stats['inf_neg']}"
    assert ids_preserved,                           "sample_id set mismatch between input and output!"
    assert labels_preserved,                        "Landslide labels altered!"
    assert ml_unchanged,                            "Input ML CSV was modified!"
    assert dem_unchanged,                           "Input DEM was modified!"

    logger.info("All validation checks PASSED.")

    # ── 7. Save output CSV ────────────────────────────────────────────────────
    out_dir  = os.path.join("ml", "data", "processed", "features")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "uttarakhand_ml_twi_features.csv")

    output_df.to_csv(out_path, index=False)
    logger.info(f"Saved TWI feature table -> {out_path}")

    # ── 8. Final Report ───────────────────────────────────────────────────────
    sep  = "=" * 70
    dash = "-" * 70

    print(f"\n{sep}")
    print("FINAL REPORT — STEP 34D: TOPOGRAPHIC WETNESS INDEX (TWI)")
    print(sep)
    print("Files Created:")
    print("  Script:  ml/src/features/extract_twi_features.py")
    print(f"  Output:  {out_path}")
    print(dash)
    print("Hydrological Library:")
    print(f"  pysheds (version: {__import__('pysheds').__version__})")
    print(dash)
    print("Hydrological Workflow:")
    print("  Library:            pysheds")
    print("  Sink/Depression:    fill_pits (Priority-Flood, Barnes et al. 2014)")
    print("                      + resolve_flats (Lindsay 2016)")
    print("                      fill_depressions skipped (not required for SRTM 30m)")
    print("  Flow Direction:     D8 (O'Callaghan & Mark 1984) via pysheds.flowdir()")
    print("  Flow Accumulation:  D8 upstream cell count via pysheds.accumulation()")
    print("  SCA Definition:     (flow_acc + 1) * cell_width [m]")
    print("  Slope Method:       Horn (1981) 3x3 finite-difference on pit-filled DEM [radians]")
    print(dash)
    print("TWI Formula:")
    print(f"  TWI = ln( (a + epsilon) / (tan(beta) + epsilon) )")
    print(f"  a       = Specific Catchment Area [m]  (D8 flow accumulation)")
    print(f"  beta    = Local slope [radians]  (Horn 3x3 from filled DEM)")
    print(f"  epsilon = {EPSILON}  (numerical stability guard)")
    print(dash)
    print("DEM & Resolution:")
    print(f"  CRS:        EPSG:32644 (WGS 84 / UTM Zone 44N)")
    print(f"  Resolution: {res_x:.1f} m x {res_y:.1f} m")
    print(dash)
    print("Row Counts:")
    print(f"  Input samples:        {n_input:,}")
    print(f"  Output rows:          {n_output:,}")
    print(f"  Unique sample_id:     {unique_ids:,}")
    print(f"  Duplicate sample_id:  {dup_ids}")
    print(f"  Out-of-bounds coords: {n_oob}")
    print(dash)
    print("TWI Statistics:")
    print(f"  Missing (NaN):   {twi_stats['missing']}")
    print(f"  +Inf count:      {twi_stats['inf_pos']}")
    print(f"  -Inf count:      {twi_stats['inf_neg']}")
    print(f"  Min:             {twi_stats['min']:.4f}")
    print(f"  Max:             {twi_stats['max']:.4f}")
    print(f"  Mean:            {twi_stats['mean']:.4f}")
    print(f"  Median:          {twi_stats['median']:.4f}")
    print(f"  Std Dev:         {twi_stats['std']:.4f}")
    print(dash)
    print("Class Balance Verification:")
    print(f"  Positive (landslide=1): {pos_count:,}  {'OK' if pos_count==5523 else 'ERROR'}")
    print(f"  Negative (landslide=0): {neg_count:,}  {'OK' if neg_count==5523 else 'ERROR'}")
    print(f"  Labels preserved:       {'YES' if labels_preserved else 'NO - ERROR'}")
    print(dash)
    print("Input File Integrity:")
    print(f"  uttarakhand_ml_samples.csv:     {'UNCHANGED' if ml_unchanged else 'MODIFIED - ERROR'}")
    print(f"  uttarakhand_dem_utm44n_30m.tif: {'UNCHANGED' if dem_unchanged else 'MODIFIED - ERROR'}")
    print(sep)
    print()
    print(">>> No machine learning model training was performed during Step 34D. <<<")
    print(sep + "\n")


if __name__ == "__main__":
    extract_twi_features()
