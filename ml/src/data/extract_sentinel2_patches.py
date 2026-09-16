"""
Step 39: Extract Sentinel-2 Surface Reflectance Harmonized RGB image patches.

Pipeline:
1. Load train_metadata.csv (8,836 samples) and test_metadata.csv (2,210 samples).
2. Connect to Google Earth Engine with project 'landslide-platform-508308'.
3. Build Sentinel-2 SR Harmonized collection (2023-01-01 to 2024-01-01), SCL cloud masking,
   and median RGB composite (B4, B3, B2).
4. For each sample, extract a 128x128 pixel patch centered at (latitude, longitude).
   Ground footprint: 128 pixels * 10 m/pixel = 1.28 km x 1.28 km.
5. Save patches to ml/data/processed/patches/<sample_id>.png.
6. Generate manifest ml/data/processed/patches/manifest.csv.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
import time
import ee
import numpy as np
import pandas as pd
from PIL import Image

PROJECT_ID = "landslide-platform-508308"
TRAIN_META_PATH = Path("ml/data/processed/splits/train_metadata.csv")
TEST_META_PATH = Path("ml/data/processed/splits/test_metadata.csv")
PATCHES_DIR = Path("ml/data/processed/patches")
MANIFEST_PATH = Path("ml/data/processed/patches/manifest.csv")

PATCH_PIXELS = 128
SCALE_METERS = 10
HALF_EXTENT_M = (PATCH_PIXELS * SCALE_METERS) / 2.0  # 640 meters
MAX_WORKERS = 30
MAX_RETRIES = 3


def initialize_ee():
    print(f"Initializing Google Earth Engine with project: {PROJECT_ID}...")
    ee.Initialize(project=PROJECT_ID)
    print("Earth Engine initialized successfully.")


def build_s2_composite():
    print("Constructing Sentinel-2 SR Harmonized 2023 Median RGB composite...")
    uttarakhand_bounds = ee.Geometry.Polygon([
        [[77.5, 28.7], [81.1, 28.7], [81.1, 31.5], [77.5, 31.5], [77.5, 28.7]]
    ])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(uttarakhand_bounds)
        .filterDate("2023-01-01", "2024-01-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    )

    def mask_scl_clouds(img):
        scl = img.select("SCL")
        # Mask out 3=cloud shadow, 8=cloud medium prob, 9=cloud high prob, 10=thin cirrus
        cloud_mask = (scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
        return img.updateMask(cloud_mask)

    rgb = (
        collection.map(mask_scl_clouds)
        .select(["B4", "B3", "B2"])  # Red, Green, Blue
        .median()
        .visualize(min=0, max=3000)   # Scale surface reflectance 0.0-0.3 to 8-bit [0, 255]
    )
    return rgb


def extract_single_patch(rgb_image, sample_id, lat, lon, target_path):
    if target_path.exists() and target_path.stat().st_size > 500:
        return sample_id, True, "cached"

    d_lat = HALF_EXTENT_M / 111000.0
    d_lon = HALF_EXTENT_M / (111000.0 * np.cos(np.radians(lat)))

    request = {
        'expression': rgb_image,
        'fileFormat': 'PNG',
        'grid': {
            'dimensions': {'width': PATCH_PIXELS, 'height': PATCH_PIXELS},
            'affineTransform': {
                'scaleX': (2 * d_lon) / PATCH_PIXELS,
                'shearX': 0,
                'translateX': lon - d_lon,
                'shearY': 0,
                'scaleY': -(2 * d_lat) / PATCH_PIXELS,
                'translateY': lat + d_lat
            },
            'crsCode': 'EPSG:4326'
        }
    }

    for attempt in range(MAX_RETRIES):
        try:
            raw_bytes = ee.data.computePixels(request)
            img = Image.open(BytesIO(raw_bytes))
            # Validate size and channels
            if img.size != (PATCH_PIXELS, PATCH_PIXELS) or img.mode != "RGB":
                img = img.convert("RGB").resize((PATCH_PIXELS, PATCH_PIXELS))
            img.save(target_path, format="PNG")
            return sample_id, True, "downloaded"
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return sample_id, False, str(e)
            time.sleep(1.0 * (attempt + 1))


def extract_all_patches(sample_limit=None):
    print("=" * 70)
    print("STEP 39 — SENTINEL-2 PATCH EXTRACTION FOR SWIN TRANSFORMER")
    print("=" * 70)

    initialize_ee()
    rgb_composite = build_s2_composite()

    PATCHES_DIR.mkdir(parents=True, exist_ok=True)

    train_meta = pd.read_csv(TRAIN_META_PATH)
    test_meta = pd.read_csv(TEST_META_PATH)

    train_meta["split"] = "train"
    test_meta["split"] = "test"

    combined = pd.concat([train_meta, test_meta], ignore_index=True)
    if sample_limit is not None:
        combined = combined.head(sample_limit)

    total_samples = len(combined)
    print(f"Total samples to process: {total_samples} (Train: {len(train_meta)}, Test: {len(test_meta)})")

    manifest_rows = []
    failed_samples = []

    print(f"Extracting patches using ThreadPoolExecutor(max_workers={MAX_WORKERS})...")
    start_time = time.time()
    completed_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_sample = {}
        for row in combined.itertuples(index=False):
            img_path = PATCHES_DIR / f"{row.sample_id}.png"
            future = executor.submit(
                extract_single_patch,
                rgb_composite,
                row.sample_id,
                float(row.latitude),
                float(row.longitude),
                img_path
            )
            future_to_sample[future] = row

        for future in as_completed(future_to_sample):
            row = future_to_sample[future]
            completed_count += 1
            sample_id, success, status = future.result()

            img_path = PATCHES_DIR / f"{row.sample_id}.png"
            if success and img_path.exists() and img_path.stat().st_size > 0:
                manifest_rows.append({
                    "sample_id": row.sample_id,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "landslide": row.landslide,
                    "split": row.split,
                    "image_path": str(img_path.as_posix())
                })
            else:
                failed_samples.append((row.sample_id, status))

            if completed_count % 500 == 0 or completed_count == total_samples:
                elapsed = time.time() - start_time
                rate = completed_count / elapsed if elapsed > 0 else 0
                print(f"Progress: {completed_count}/{total_samples} patches processed ({rate:.1f} patches/sec)...")

    # Save manifest
    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_csv(MANIFEST_PATH, index=False)
    print(f"\nSaved patch manifest with {len(manifest_df)} records to {MANIFEST_PATH}")
    if failed_samples:
        print(f"Warning: {len(failed_samples)} samples failed extraction: {failed_samples[:5]}")
    else:
        print("All patches extracted successfully with 0 failures!")


if __name__ == "__main__":
    extract_all_patches()
