import pandas as pd
from pathlib import Path

output_path = Path("ml/reports/tft_temporal_schema.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

data = [
    {
        "field_name": "history",
        "source_dataset": "uttarakhand_landslide_inventory_clean.csv",
        "data_type": "object (string)",
        "total_records": 5523,
        "non_null_count": 2053,
        "null_count": 3470,
        "missing_percentage": 62.83,
        "unique_values_count": 185,
        "min_value": "1998",
        "max_value": "2025",
        "representative_examples": "2014; 16th-17th June 2013; 2018; August 2023; 30 June, 2016",
        "temporal_semantics": "Historical field survey notes / retrospective inquiry; 74.6% of present values are coarse 4-digit years; only 8.5% have dates",
        "tft_suitability": "Inadequate for point supervision (>62% missing, 75% of non-null are year-only)"
    },
    {
        "field_name": "slide_no",
        "source_dataset": "uttarakhand_landslide_inventory_clean.csv",
        "data_type": "object (string)",
        "total_records": 5523,
        "non_null_count": 5522,
        "null_count": 1,
        "missing_percentage": 0.02,
        "unique_values_count": 5518,
        "min_value": "2013",
        "max_value": "2025",
        "representative_examples": "UK/CHA/62C04/2017/34; UK/CHA/53O16/2015/12; UK/UTT/53J06/2018/1",
        "temporal_semantics": "GSI Field Season Programme (FSP) mapping campaign year; reflects survey/inventory observation time, NOT landslide failure event date",
        "tft_suitability": "Non-event metadata (survey administration year, not failure timestamp)"
    },
    {
        "field_name": "landslide_date",
        "source_dataset": "uttarakhand_master_ml_dataset.csv",
        "data_type": "None (non-existent)",
        "total_records": 11046,
        "non_null_count": 0,
        "null_count": 11046,
        "missing_percentage": 100.0,
        "unique_values_count": 0,
        "min_value": "N/A",
        "max_value": "N/A",
        "representative_examples": "Field does not exist in master ML dataset or splits",
        "temporal_semantics": "No temporal feature or target exists in master dataset",
        "tft_suitability": "Missing entirely"
    },
    {
        "field_name": "negative_sample_timestamp",
        "source_dataset": "uttarakhand_negative_samples.csv",
        "data_type": "None (non-existent)",
        "total_records": 5523,
        "non_null_count": 0,
        "null_count": 5523,
        "missing_percentage": 100.0,
        "unique_values_count": 0,
        "min_value": "N/A",
        "max_value": "N/A",
        "representative_examples": "UK_NEG_00001 (lat: 29.864824, lon: 80.306968, landslide: 0)",
        "temporal_semantics": "Negative samples represent static spatial pseudo-absences (>2km from known slides); zero temporal timestamps exist",
        "tft_suitability": "Cannot construct dynamic non-event rainfall sequences without arbitrary date invention"
    },
    {
        "field_name": "mean_annual_precipitation_mm",
        "source_dataset": "features/uttarakhand_ml_precipitation_features.csv",
        "data_type": "float64",
        "total_records": 11046,
        "non_null_count": 11046,
        "null_count": 0,
        "missing_percentage": 0.0,
        "unique_values_count": 875,
        "min_value": "394.21 mm",
        "max_value": "2468.61 mm",
        "representative_examples": "1468.5 mm; 1184.2 mm; 1823.1 mm",
        "temporal_semantics": "Static 10-year climatological normal (2014-2023 mean annual total from CHIRPS Daily); static environmental susceptibility feature, not dynamic sequence",
        "tft_suitability": "Static terrain branch feature; raw daily sequences are not stored locally"
    }
]

df = pd.DataFrame(data)
df.to_csv(output_path, index=False)
print(f"Saved temporal schema audit table to {output_path}")
