import os
import sys
import logging
import re
import pandas as pd
import pdfplumber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_pdf_path():
    """Locate the Bhusanket landslide inventory PDF file."""
    candidate_paths = [
        os.path.join("ml", "data", "raw", "landslide_report.pdf"),
        os.path.join("data", "raw", "landslide_report.pdf"),
        "landslide_report.pdf",
        r"C:\Users\hp\OneDrive\Desktop\Landslide\landslide-platform\ml\data\raw\landslide_report.pdf",
        r"C:\Users\hp\Downloads\Landslide_Datasets\landslide_report.pdf"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            logger.info(f"Found PDF file at: {path}")
            return path
    raise FileNotFoundError("Could not locate landslide_report.pdf file in raw data directory.")

def clean_text(val):
    """Clean string values from PDF extraction."""
    if val is None:
        return ""
    val_str = str(val).strip()
    # Replace multiple newlines or tabs with a single space
    val_str = re.sub(r'\s+', ' ', val_str)
    return val_str

def parse_coordinate(val):
    """Parse numeric coordinate float value from string."""
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() in ["NA", "N/A", "NONE", "NULL", "-"]:
        return None
    try:
        # Extract first floating point number pattern
        match = re.search(r'[-+]?\d*\.\d+|\d+', val_str)
        if match:
            return float(match.group())
    except (ValueError, TypeError):
        pass
    return None

def is_valid_geo_coordinate(lat, lon):
    """Validate if latitude and longitude are valid geographic coordinates."""
    if lat is None or lon is None:
        return False
    if not (-90.0 <= lat <= 90.0):
        return False
    if not (-180.0 <= lon <= 180.0):
        return False
    return True

def extract_uttarakhand_landslides():
    """Programmatically extract Uttarakhand landslide records from GSI Bhusanket PDF."""
    pdf_path = find_pdf_path()
    output_dir = os.path.join("ml", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "uttarakhand_landslide_inventory.csv")

    raw_extracted_records = []
    
    logger.info("Opening PDF with pdfplumber for table extraction...")
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"PDF opened successfully. Total pages: {total_pages}")
        
        # Scan pages (pages 780 to 904 contain Uttarakhand records)
        start_page = max(0, 780)
        end_page = total_pages
        
        logger.info(f"Scanning pages {start_page + 1} to {end_page} for Uttarakhand records...")
        for page_idx in range(start_page, end_page):
            page = pdf.pages[page_idx]
            page_text = page.extract_text() or ""
            
            # Fast check if Uttarakhand is on this page
            if "uttarakhand" not in page_text.lower():
                continue

            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Expecting 11 columns header:
                    # Sl.No.(0), Slide_No(1), State(2), District(3), Slide_Name(4),
                    # NH_SH_Location(5), Latitude(6), Longitude(7), Material Involved(8),
                    # Movement Type(9), History(10)
                    if len(row) >= 11:
                        state_val = clean_text(row[2])
                        if "uttarakhand" in state_val.lower():
                            slide_no = clean_text(row[1])
                            district = clean_text(row[3])
                            slide_name = clean_text(row[4])
                            raw_lat = clean_text(row[6])
                            raw_lon = clean_text(row[7])
                            material = clean_text(row[8])
                            movement = clean_text(row[9])
                            history = clean_text(row[10])

                            raw_extracted_records.append({
                                "slide_no": slide_no,
                                "district": district,
                                "slide_name": slide_name,
                                "latitude": raw_lat,
                                "longitude": raw_lon,
                                "material_involved": material,
                                "movement_type": movement,
                                "history": history,
                                "landslide": 1
                            })

    total_extracted_raw = len(raw_extracted_records)
    logger.info(f"Extraction complete! Raw Uttarakhand records extracted: {total_extracted_raw}")

    if total_extracted_raw == 0:
        logger.warning("No Uttarakhand records were extracted from the PDF!")
        return

    # Convert to pandas DataFrame for cleaning & validation
    df = pd.DataFrame(raw_extracted_records)

    # 1. Coordinate parsing & validation
    df['latitude_num'] = df['latitude'].apply(parse_coordinate)
    df['longitude_num'] = df['longitude'].apply(parse_coordinate)

    # Validate numeric and geographic coordinate boundaries
    valid_coord_mask = df.apply(
        lambda r: is_valid_geo_coordinate(r['latitude_num'], r['longitude_num']), axis=1
    )

    invalid_coord_count = int((~valid_coord_mask).sum())
    logger.info(f"Rows removed due to missing or invalid numeric coordinates: {invalid_coord_count}")

    # Retain valid coordinates
    df_valid = df[valid_coord_mask].copy()
    df_valid['latitude'] = df_valid['latitude_num']
    df_valid['longitude'] = df_valid['longitude_num']

    # 2. Duplicate Removal
    # Define duplicate check columns
    dedup_cols = ['slide_no', 'district', 'slide_name', 'latitude', 'longitude']
    initial_valid_count = len(df_valid)
    df_clean = df_valid.drop_duplicates(subset=dedup_cols, keep='first').copy()
    duplicates_removed_count = initial_valid_count - len(df_clean)
    logger.info(f"Duplicate records removed: {duplicates_removed_count}")

    # 3. Final Column Formatting
    target_columns = [
        'slide_no',
        'district',
        'slide_name',
        'latitude',
        'longitude',
        'material_involved',
        'movement_type',
        'history',
        'landslide'
    ]

    df_final = df_clean[target_columns].reset_index(drop=True)

    # Save to CSV
    df_final.to_csv(output_csv, index=False)
    logger.info(f"Saved processed dataset to: {output_csv}")
    logger.info(f"Final valid Uttarakhand records saved: {len(df_final)}")

    # Display Metrics Summary
    print("\n" + "="*50)
    print("EXTRACTION & VALIDATION METRICS SUMMARY")
    print("="*50)
    print(f"1. PDF Extraction Library Used: pdfplumber (v0.11.10)")
    print(f"2. Total Uttarakhand Records Extracted: {total_extracted_raw}")
    print(f"3. Rows Removed (Missing/Invalid Coordinates): {invalid_coord_count}")
    print(f"4. Duplicate Rows Removed: {duplicates_removed_count}")
    print(f"5. Final Valid Records Saved: {len(df_final)}")
    print(f"6. Output CSV Path: {output_csv}")
    print(f"7. Final CSV Columns: {list(df_final.columns)}")
    print("="*50)
    print("\nPreview of First 10 Rows:")
    print(df_final.head(10).to_string())

if __name__ == "__main__":
    extract_uttarakhand_landslides()
