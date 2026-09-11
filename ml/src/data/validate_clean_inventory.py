import os
import sys
import logging
import re
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

def find_input_csv():
    """Locate the extracted Uttarakhand landslide inventory CSV file."""
    candidate_paths = [
        os.path.join("ml", "data", "processed", "uttarakhand_landslide_inventory.csv"),
        os.path.join("data", "processed", "uttarakhand_landslide_inventory.csv"),
        "uttarakhand_landslide_inventory.csv"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            logger.info(f"Found input CSV file at: {path}")
            return path
    raise FileNotFoundError("Could not locate uttarakhand_landslide_inventory.csv file.")

def clean_string(val):
    """Trim leading/trailing whitespace, normalize internal whitespace, preserve NaN/null."""
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip()
    s = re.sub(r'\s+', ' ', s)
    if not s or s.lower() in ['nan', 'null', 'none', 'blank', '']:
        return np.nan
    return s

def normalize_material_involved(val):
    """
    Normalize material_involved categories consistently while preserving semantic meaning.
    Preserves missing values as np.nan.
    """
    s = clean_string(val)
    if pd.isna(s):
        return np.nan

    # Standardize spacing around slashes, pluses, ampersands
    s_clean = re.sub(r'\s*/\s*', '/', s)
    s_clean = re.sub(r'\s*\+\s*', ' + ', s_clean)
    s_clean = re.sub(r'\s*&\s*', ' & ', s_clean)
    # Standardize 'Rock cum Debris' variations (e.g. 'Rock-cum-debris', 'rock-cum-debris')
    s_clean = re.sub(r'(?i)\brock[- ]cum[- ]debris\b', 'Rock cum Debris', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()

    canonical_map = {
        'rock': 'Rock',
        'debris': 'Debris',
        'soil': 'Soil',
        'earth': 'Earth',
        'rbm': 'RBM',
        'rock cum debris': 'Rock cum Debris',
        'debris cum earth': 'Debris cum Earth',
        'earth cum rock': 'Earth cum Rock',
        'debris flow': 'Debris Flow',
        'rock boulder': 'Rock Boulder',
        'rock boulders': 'Rock Boulders',
        'slope wash material': 'Slope Wash Material',
        'river borne material': 'River Borne Material',
        'river borne and slope wash material': 'River Borne and Slope Wash Material',
        'overburden and rbm': 'Overburden and RBM',
        'muck/fill material': 'Muck/fill Material',
        'debris and weathered rock': 'Debris and Weathered Rock',
        'debris/bank erosion': 'Debris/Bank Erosion',
        'unconsolidated colluvial debris': 'Unconsolidated Colluvial Debris',
        'fluvio- glacial material': 'Fluvio-Glacial Material',
        'fluvio-glacial material': 'Fluvio-Glacial Material',
        'rock and debris': 'Rock and Debris',
        'rock & debris': 'Rock & Debris',
        'rock + debris': 'Rock + Debris',
        'soil/debris': 'Soil/Debris',
        'soil & debis': 'Soil & Debis',
        'debris/soil': 'Debris/Soil',
        'rock/debris': 'Rock/Debris',
        'rock(nala)': 'Rock (Nala)',
        'rock (biotite gneiss)': 'Rock (Biotite Gneiss)',
        'rock, rbm and slope wash material.': 'Rock, RBM and Slope Wash Material',
        'overburden/debris, soil and rbm': 'Overburden/Debris, Soil and RBM',
        'rock + debris (complex)': 'Rock + Debris (Complex)',
        'rock, debris': 'Rock, Debris'
    }

    s_lower = s_clean.lower()
    if s_lower in canonical_map:
        return canonical_map[s_lower]

    return s_clean.title()

def normalize_movement_type(val):
    """
    Normalize movement_type categories consistently while preserving semantic meaning.
    Preserves missing values as np.nan.
    """
    s = clean_string(val)
    if pd.isna(s):
        return np.nan

    # Standardize spacing around slashes, pluses, ampersands
    s_clean = re.sub(r'\s*/\s*', '/', s)
    s_clean = re.sub(r'\s*\+\s*', ' + ', s_clean)
    s_clean = re.sub(r'\s*&\s*', ' & ', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()

    canonical_map = {
        'slide': 'Slide',
        'fall': 'Fall',
        'falls': 'Falls',
        'flow': 'Flow',
        'flows': 'Flows',
        'subsidence': 'Subsidence',
        'topple': 'Topple',
        'composite': 'Composite',
        'slump': 'Slump',
        'creep': 'Creep',
        'spread': 'Spread',
        'rotational': 'Rotational',
        'lateral spread': 'Lateral Spread',
        'debris flow': 'Debris Flow',
        'debris slide': 'Debris Slide',
        'fall and slide': 'Fall and Slide',
        'fall & slide': 'Fall & Slide',
        'fall and flow': 'Fall and Flow',
        'slide and flow': 'Slide and Flow',
        'slide & flow': 'Slide & Flow',
        'slide + fall': 'Slide + Fall',
        'slide & fall': 'Slide & Fall',
        'rock fall': 'Rock Fall',
        'rock slide': 'Rock Slide',
        'fall/topple': 'Fall/Topple',
        'slide/subsidence': 'Slide/Subsidence',
        'slide/creep': 'Slide/Creep',
        'topple slide': 'Topple Slide',
        'subsidence (20- 30 m)': 'Subsidence (20-30 m)',
        'subsidence (20-30 m)': 'Subsidence (20-30 m)',
        'slide and subsidence': 'Slide and Subsidence',
        'slide & subsidence': 'Slide & Subsidence',
        'slide subsidence': 'Slide Subsidence',
        'creep & subsidence & slide at part': 'Creep & Subsidence & Slide at part',
        'flow (debris)': 'Flow (Debris)',
        'subsidence and sinking': 'Subsidence and Sinking',
        'debris, subsidence, rotational.': 'Debris, Subsidence, Rotational',
        'falls, slide': 'Falls, Slide',
        'rock fall + rock slide': 'Rock Fall + Rock Slide'
    }

    s_lower = s_clean.lower()
    if s_lower in canonical_map:
        return canonical_map[s_lower]

    return s_clean.title()

def extract_years_from_history(history_series):
    """Parse 4-digit years from history text."""
    years = []
    for val in history_series.dropna():
        s = str(val).strip()
        matches = re.findall(r'(19\d\d|20\d\d)', s)
        if matches:
            years.extend([int(m) for m in matches])
    return pd.Series(years, dtype=int)

def generate_quality_report(df):
    """Generate comprehensive initial data quality report."""
    print("=" * 60)
    print("RAW DATASET DATA QUALITY REPORT")
    print("=" * 60)
    print(f"Total Rows: {len(df)}")
    print(f"Column Names: {list(df.columns)}")
    print("\nData Types:")
    print(df.dtypes)
    print("\nMissing Values per Column:")
    print(df.isna().sum())
    
    full_dups = df.duplicated().sum()
    print(f"\nDuplicate Full Rows: {full_dups}")
    
    coord_dups_mask = df.duplicated(subset=['latitude', 'longitude'], keep=False)
    dup_coords_count = df.duplicated(subset=['latitude', 'longitude']).sum()
    unique_dup_coord_groups = df[coord_dups_mask].groupby(['latitude', 'longitude']).ngroups
    print(f"Duplicate Coordinate Pairs: {dup_coords_count} additional occurrences ({unique_dup_coord_groups} unique groups, {coord_dups_mask.sum()} total rows)")
    
    print(f"\nUnique District Count: {df['district'].nunique()}")
    print("District Distribution:")
    print(df['district'].value_counts(dropna=False))
    
    print(f"\nLatitude Range: [{df['latitude'].min()}, {df['latitude'].max()}]")
    print(f"Longitude Range: [{df['longitude'].min()}, {df['longitude'].max()}]")
    
    print("\nMaterial Involved Distribution (Raw):")
    print(df['material_involved'].value_counts(dropna=False))
    
    print("\nMovement Type Distribution (Raw):")
    print(df['movement_type'].value_counts(dropna=False))
    
    parsed_years = extract_years_from_history(df['history'])
    print(f"\nHistory / Year Distribution (Parseable years: {len(parsed_years)} total instances):")
    print(parsed_years.value_counts().sort_index())
    print("=" * 60 + "\n")

def investigate_coordinate_duplicates(df, meaningful_cols):
    """Investigate all duplicate coordinate pairs in detail before cleaning."""
    coord_dups_mask = df.duplicated(subset=['latitude', 'longitude'], keep=False)
    coord_groups = df[coord_dups_mask].groupby(['latitude', 'longitude'])
    
    logger.info("=" * 60)
    logger.info(f"DUPLICATE COORDINATE INVESTIGATION ({len(coord_groups)} unique coordinate pairs)")
    logger.info("=" * 60)
    
    investigation_summary = []
    
    for i, ((lat, lon), group) in enumerate(coord_groups, 1):
        num_records = len(group)
        unique_slide_no = group['slide_no'].dropna().unique().tolist()
        group_meaningful = group[meaningful_cols]
        is_otherwise_identical = (len(group_meaningful.drop_duplicates()) == 1)
        district_differs = (group['district'].nunique(dropna=False) > 1)
        history_differs = (group['history'].nunique(dropna=False) > 1)
        
        info = {
            'group_id': i,
            'latitude': lat,
            'longitude': lon,
            'num_records': num_records,
            'unique_slide_no_count': len(unique_slide_no),
            'unique_slide_nos': unique_slide_no,
            'is_otherwise_identical': is_otherwise_identical,
            'district_differs': district_differs,
            'history_differs': history_differs
        }
        investigation_summary.append(info)
        
        logger.info(
            f"Group {i:02d} | Coords: ({lat:.6f}, {lon:.6f}) | Records: {num_records} | "
            f"Unique slide_no: {len(unique_slide_no)} | Identical across meaningful cols: {is_otherwise_identical} | "
            f"District differs: {district_differs} | History differs: {history_differs}"
        )
        
    logger.info("=" * 60)
    return investigation_summary, coord_groups

def main():
    logger.info("Starting Uttarakhand Landslide Inventory Validation & Cleaning Pipeline...")
    
    # 1. Load original CSV
    input_csv_path = find_input_csv()
    df_raw = pd.read_csv(input_csv_path)
    original_rows = len(df_raw)
    logger.info(f"Successfully loaded input dataset with {original_rows} rows.")
    
    # 2. Initial Data Quality Report
    generate_quality_report(df_raw)
    
    # 3. Categorical & String Normalization
    logger.info("Normalizing string & categorical fields...")
    df_clean = df_raw.copy()
    
    df_clean['slide_no'] = df_clean['slide_no'].apply(clean_string)
    df_clean['district'] = df_clean['district'].apply(clean_string)
    df_clean['slide_name'] = df_clean['slide_name'].apply(clean_string)
    df_clean['material_involved'] = df_clean['material_involved'].apply(normalize_material_involved)
    df_clean['movement_type'] = df_clean['movement_type'].apply(normalize_movement_type)
    df_clean['history'] = df_clean['history'].apply(clean_string)
    df_clean['landslide'] = df_clean['landslide'].astype(int)
    
    # Meaningful fields for deduplication evaluation
    meaningful_cols = [
        'slide_no', 'district', 'slide_name', 'latitude', 'longitude',
        'material_involved', 'movement_type', 'history', 'landslide'
    ]
    
    # 4. Investigate Duplicate Coordinates before deduplication
    investigation_summary, coord_groups = investigate_coordinate_duplicates(df_clean, meaningful_cols)
    coordinate_duplicates_investigated = len(coord_groups)
    
    # 5. Apply Deduplication Rule
    # Rule: Remove exact duplicates where ALL meaningful fields match after normalization.
    # Preserve records sharing coordinates if they differ in any meaningful field.
    
    # First: Exact duplicate records across all meaningful fields
    exact_dup_mask = df_clean.duplicated(subset=meaningful_cols, keep='first')
    exact_duplicates_removed = int(exact_dup_mask.sum())
    
    if exact_duplicates_removed > 0:
        logger.info(f"Removing {exact_duplicates_removed} exact duplicate records...")
        df_clean = df_clean[~exact_dup_mask].reset_index(drop=True)
    else:
        logger.info("No exact duplicate records found across all meaningful fields.")
        
    # Second: Check coordinate duplicate groups for identical records
    coordinate_duplicates_removed = 0
    rows_to_drop = []
    
    for (lat, lon), group in df_clean.groupby(['latitude', 'longitude']):
        if len(group) > 1:
            group_meaningful = group[meaningful_cols]
            # If all records in this coordinate group are 100% identical across meaningful fields
            if len(group_meaningful.drop_duplicates()) == 1:
                # Keep first record, mark remaining for removal
                indices_to_drop = group.index.tolist()[1:]
                rows_to_drop.extend(indices_to_drop)
                coordinate_duplicates_removed += len(indices_to_drop)
                
    if rows_to_drop:
        logger.info(f"Removing {coordinate_duplicates_removed} duplicate coordinate records with identical information...")
        df_clean = df_clean.drop(index=rows_to_drop).reset_index(drop=True)
    else:
        logger.info("All duplicate coordinate records contain distinct meaningful inventory information. Preserving all original records.")
        
    final_rows = len(df_clean)
    
    # 6. Validate Coordinates & Labels post-cleaning
    logger.info("Validating coordinates and landslide labels post-cleaning...")
    
    # Coordinate range validation
    invalid_lat = df_clean[(df_clean['latitude'] < -90.0) | (df_clean['latitude'] > 90.0) | df_clean['latitude'].isna()]
    invalid_lon = df_clean[(df_clean['longitude'] < -180.0) | (df_clean['longitude'] > 180.0) | df_clean['longitude'].isna()]
    
    if not invalid_lat.empty:
        raise ValueError(f"Validation Error: Found {len(invalid_lat)} invalid latitude values.")
    if not invalid_lon.empty:
        raise ValueError(f"Validation Error: Found {len(invalid_lon)} invalid longitude values.")
        
    # Landslide label validation
    non_one_landslide = df_clean[df_clean['landslide'] != 1]
    if not non_one_landslide.empty:
        raise ValueError(f"Validation Error: Found {len(non_one_landslide)} rows where landslide label is not 1.")
        
    logger.info("All coordinate range and label validation checks PASSED successfully.")
    
    # 7. Save Clean Output CSV
    output_dir = os.path.join("ml", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, "uttarakhand_landslide_inventory_clean.csv")
    
    df_clean.to_csv(output_csv_path, index=False)
    logger.info(f"Successfully saved cleaned inventory dataset to: {output_csv_path}")
    
    # 8. Print Concise Final Report
    print("\n" + "=" * 60)
    print("CONCISE FINAL REPORT: UTTARAKHAND LANDSLIDE INVENTORY CLEANING")
    print("=" * 60)
    print(f"ORIGINAL_ROWS: {original_rows}")
    print(f"EXACT_DUPLICATES_REMOVED: {exact_duplicates_removed}")
    print(f"COORDINATE_DUPLICATES_INVESTIGATED: {coordinate_duplicates_investigated}")
    print(f"COORDINATE_DUPLICATES_REMOVED: {coordinate_duplicates_removed}")
    print(f"FINAL_ROWS: {final_rows}")
    print("-" * 60)
    print("Missing Values After Cleaning:")
    print(df_clean.isna().sum().to_string())
    print("-" * 60)
    print(f"Final Latitude Range: [{df_clean['latitude'].min()}, {df_clean['latitude'].max()}]")
    print(f"Final Longitude Range: [{df_clean['longitude'].min()}, {df_clean['longitude'].max()}]")
    print(f"Number of Unique Districts: {df_clean['district'].nunique()}")
    print("-" * 60)
    print("Normalized material_involved Categories:")
    print(df_clean['material_involved'].value_counts(dropna=False).to_string())
    print("-" * 60)
    print("Normalized movement_type Categories:")
    print(df_clean['movement_type'].value_counts(dropna=False).to_string())
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
