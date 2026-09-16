"""
Step 36: ML Preprocessing and Train/Test Dataset Preparation
for Uttarakhand Landslide Susceptibility Modeling.

Workflow:
    1. Load and validate authoritative master ML dataset (uttarakhand_master_ml_dataset.csv).
    2. Engineer circular aspect features (aspect_sin, aspect_cos) and drop raw aspect_degrees.
    3. Separate metadata (sample_id, latitude, longitude) and target (landslide).
    4. Perform stratified train/test split (80/20, random_state=42) BEFORE fitting transformers.
    5. Construct leakage-safe scikit-learn ColumnTransformer:
       - Numeric pipeline: SimpleImputer(strategy="median")
       - Categorical pipeline: SimpleImputer(strategy="most_frequent") -> OneHotEncoder(handle_unknown="ignore")
    6. Fit ColumnTransformer ONLY on training predictors (X_train_raw).
    7. Transform both X_train and X_test using the fitted pipeline.
    8. Extract transformed feature names and format as DataFrames.
    9. Run comprehensive post-processing validation suite.
    10. Save transformed splits to ml/data/processed/splits/:
        - X_train.csv, X_test.csv, y_train.csv, y_test.csv, train_metadata.csv, test_metadata.csv
    11. Save fitted pipeline and feature manifest to ml/models/preprocessing/:
        - preprocessing_pipeline.joblib, feature_names.json
    12. Print detailed execution and validation report.
"""

import json
from pathlib import Path
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# CONFIGURATION AND CONSTANTS
# ============================================================

MASTER_DATASET_PATH = Path("ml/data/processed/uttarakhand_master_ml_dataset.csv")

SPLITS_DIR = Path("ml/data/processed/splits")
MODELS_PREPROCESSING_DIR = Path("ml/models/preprocessing")

PIPELINE_OUTPUT_PATH = MODELS_PREPROCESSING_DIR / "preprocessing_pipeline.joblib"
FEATURE_MANIFEST_PATH = MODELS_PREPROCESSING_DIR / "feature_names.json"

EXPECTED_ROW_COUNT = 11046
EXPECTED_COL_COUNT = 13
EXPECTED_POS_COUNT = 5523
EXPECTED_NEG_COUNT = 5523

TEST_SIZE = 0.20
RANDOM_STATE = 42

AUTHORITATIVE_COLUMNS = [
    "sample_id",
    "latitude",
    "longitude",
    "elevation_m",
    "slope_degrees",
    "aspect_degrees",
    "profile_curvature",
    "plan_curvature",
    "twi",
    "ndvi",
    "lulc_class",
    "mean_annual_precipitation_mm",
    "landslide",
]

# Raw numeric features before aspect transformation
RAW_NUMERIC_FEATURES = [
    "elevation_m",
    "slope_degrees",
    "aspect_degrees",
    "profile_curvature",
    "plan_curvature",
    "twi",
    "ndvi",
    "mean_annual_precipitation_mm",
]

# Engineered circular features
ENGINEERED_CIRCULAR_FEATURES = ["aspect_sin", "aspect_cos"]

# Final numeric features to pass into ColumnTransformer
FINAL_NUMERIC_FEATURES = [
    "elevation_m",
    "slope_degrees",
    "profile_curvature",
    "plan_curvature",
    "twi",
    "ndvi",
    "mean_annual_precipitation_mm",
    "aspect_sin",
    "aspect_cos",
]

CATEGORICAL_FEATURES = ["lulc_class"]
METADATA_COLUMNS = ["sample_id", "latitude", "longitude", "landslide"]
TARGET_COLUMN = "landslide"


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    start_time = time.time()

    print("=" * 80, flush=True)
    print("STEP 36 — ML PREPROCESSING AND TRAIN/TEST DATASET PREPARATION", flush=True)
    print("=" * 80, flush=True)

    # --------------------------------------------------------
    # 1. Load and Validate Master Dataset
    # --------------------------------------------------------
    print(f"\n[1/7] Loading and validating master dataset: {MASTER_DATASET_PATH}...", flush=True)
    if not MASTER_DATASET_PATH.exists():
        raise FileNotFoundError(f"Master dataset missing: {MASTER_DATASET_PATH}")

    # Track master dataset immutability
    master_mtime_before = MASTER_DATASET_PATH.stat().st_mtime
    master_size_before = MASTER_DATASET_PATH.stat().st_size

    df = pd.read_csv(MASTER_DATASET_PATH)

    # Validate row and column count
    if len(df) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Validation Failure: Expected {EXPECTED_ROW_COUNT} rows, got {len(df)}")
    initial_row_count = len(df)
    initial_col_count = len(df.columns)
    if initial_col_count != EXPECTED_COL_COUNT:
        raise ValueError(f"Validation Failure: Expected {EXPECTED_COL_COUNT} columns, got {initial_col_count}")
    if list(df.columns) != AUTHORITATIVE_COLUMNS:
        raise ValueError(f"Validation Failure: Column order mismatch. Got {list(df.columns)}")

    # Validate sample_id uniqueness
    if df["sample_id"].nunique() != EXPECTED_ROW_COUNT:
        raise ValueError("Validation Failure: sample_id values are not unique")
    dup_sample_ids = int(df["sample_id"].duplicated().sum())
    if dup_sample_ids != 0:
        raise ValueError(f"Validation Failure: Found {dup_sample_ids} duplicate sample IDs")

    # Validate target labels and class balance
    unique_labels = set(df[TARGET_COLUMN].unique())
    if not unique_labels.issubset({0, 1}):
        raise ValueError(f"Validation Failure: Target labels contain unexpected values: {unique_labels}")

    pos_count_init = int((df[TARGET_COLUMN] == 1).sum())
    neg_count_init = int((df[TARGET_COLUMN] == 0).sum())
    if pos_count_init != EXPECTED_POS_COUNT or neg_count_init != EXPECTED_NEG_COUNT:
        raise ValueError(f"Validation Failure: Class counts altered: pos={pos_count_init}, neg={neg_count_init}")

    # Check infinite values across numeric features
    for col in RAW_NUMERIC_FEATURES:
        vals = df[col].values.astype(float)
        inf_count = int(np.isposinf(vals).sum() + np.isneginf(vals).sum())
        if inf_count > 0:
            raise ValueError(f"Validation Failure: Master dataset column '{col}' contains {inf_count} infinite values")

    print(f"  Master dataset validated: {len(df):,} rows, {len(df.columns)} columns", flush=True)
    print(f"  Class balance: Positive={pos_count_init:,} (50.0%), Negative={neg_count_init:,} (50.0%)", flush=True)

    # --------------------------------------------------------
    # 2. Feature Engineering — Aspect Circular Transformation
    # --------------------------------------------------------
    print("\n[2/7] Performing circular transformation for aspect_degrees...", flush=True)
    # IMPORTANT: Do NOT impute before transformation. If aspect_degrees is NaN, sin/cos must remain NaN.
    aspect_rad = np.deg2rad(df["aspect_degrees"])
    df["aspect_sin"] = np.sin(aspect_rad)
    df["aspect_cos"] = np.cos(aspect_rad)

    # Verify that missing aspect_degrees mapped strictly to missing aspect_sin and aspect_cos
    raw_aspect_nan = df["aspect_degrees"].isna()
    if not (df["aspect_sin"].isna() == raw_aspect_nan).all():
        raise ValueError("Discrepancy between aspect_degrees NaN and aspect_sin NaN")
    if not (df["aspect_cos"].isna() == raw_aspect_nan).all():
        raise ValueError("Discrepancy between aspect_degrees NaN and aspect_cos NaN")

    # Drop raw aspect_degrees from the candidate feature set
    df_engineered = df.drop(columns=["aspect_degrees"])
    print(f"  Engineered 'aspect_sin' and 'aspect_cos'. Dropped 'aspect_degrees'.", flush=True)
    print(f"  Aspect missing count before imputation: {raw_aspect_nan.sum()} samples", flush=True)

    # --------------------------------------------------------
    # 3. Stratified Train/Test Split
    # --------------------------------------------------------
    print(f"\n[3/7] Performing stratified train/test split (test_size={TEST_SIZE:.2f}, random_state={RANDOM_STATE})...", flush=True)
    # Split the full engineered DataFrame to preserve metadata alignment
    train_df, test_df = train_test_split(
        df_engineered,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df_engineered[TARGET_COLUMN],
    )

    n_train = len(train_df)
    n_test = len(test_df)
    print(f"  Training samples : {n_train:,} ({n_train / len(df):.1%})", flush=True)
    print(f"  Testing samples  : {n_test:,} ({n_test / len(df):.1%})", flush=True)

    # Validate split properties
    if n_train + n_test != EXPECTED_ROW_COUNT:
        raise ValueError(f"Split row sum {n_train + n_test} != {EXPECTED_ROW_COUNT}")

    train_ids = set(train_df["sample_id"])
    test_ids = set(test_df["sample_id"])
    overlap_ids = train_ids.intersection(test_ids)
    if overlap_ids:
        raise ValueError(f"Data Leakage Violation: {len(overlap_ids)} sample IDs overlap between train and test!")

    union_ids = train_ids.union(test_ids)
    if union_ids != set(df["sample_id"]):
        raise ValueError("Train/test union does not equal the original sample IDs set")

    train_pos = int((train_df[TARGET_COLUMN] == 1).sum())
    train_neg = int((train_df[TARGET_COLUMN] == 0).sum())
    test_pos = int((test_df[TARGET_COLUMN] == 1).sum())
    test_neg = int((test_df[TARGET_COLUMN] == 0).sum())

    print(f"  Train class distribution: Pos={train_pos:,} ({train_pos/n_train:.2%}), Neg={train_neg:,} ({train_neg/n_train:.2%})", flush=True)
    print(f"  Test class distribution : Pos={test_pos:,} ({test_pos/n_test:.2%}), Neg={test_neg:,} ({test_neg/n_test:.2%})", flush=True)

    # Record missing values before preprocessing
    train_missing_before = train_df[FINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES].isna().sum()
    test_missing_before = test_df[FINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES].isna().sum()

    # Extract metadata tables
    train_metadata = train_df[METADATA_COLUMNS].copy()
    test_metadata = test_df[METADATA_COLUMNS].copy()

    y_train = train_df[[TARGET_COLUMN]].copy()
    y_test = test_df[[TARGET_COLUMN]].copy()

    X_train_raw = train_df[FINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    X_test_raw = test_df[FINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()

    # --------------------------------------------------------
    # 4. Construct and Fit Preprocessing Pipeline
    # --------------------------------------------------------
    print("\n[4/7] Constructing and fitting scikit-learn ColumnTransformer...", flush=True)
    print("  Numeric pipeline: SimpleImputer(strategy='median')", flush=True)
    print("  Categorical pipeline: SimpleImputer(strategy='most_frequent') -> OneHotEncoder(handle_unknown='ignore')", flush=True)
    print("  NOTE: Universal scaling is intentionally omitted (model-specific scalers will be applied later).", flush=True)

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    # Version-compatible OneHotEncoder configuration for dense array output
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", ohe),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", num_pipeline, FINAL_NUMERIC_FEATURES),
            ("categorical", cat_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )

    # CRITICAL LEAKAGE CHECK: Fit ONLY on X_train_raw
    print("  Fitting preprocessor ONLY on X_train...", flush=True)
    preprocessor.fit(X_train_raw)
    print("  Preprocessor successfully fit on training data without leakage.", flush=True)

    # --------------------------------------------------------
    # 5. Transform Datasets and Extract Feature Names
    # --------------------------------------------------------
    print("\n[5/7] Transforming train and test predictor matrices...", flush=True)
    X_train_transformed_arr = preprocessor.transform(X_train_raw)
    X_test_transformed_arr = preprocessor.transform(X_test_raw)

    # Extract final feature names
    transformed_feature_names = list(preprocessor.get_feature_names_out())
    n_features = len(transformed_feature_names)
    print(f"  Total transformed ML features: {n_features}", flush=True)

    # Discover LULC categories learned during fit
    cat_transformer = preprocessor.named_transformers_["categorical"]
    ohe_fitted = cat_transformer.named_steps["onehot"]
    learned_lulc_categories = [float(c) for c in ohe_fitted.categories_[0]]
    print(f"  LULC categories learned from training data ({len(learned_lulc_categories)}): {learned_lulc_categories}", flush=True)

    # Convert back to DataFrames with exact column names and index alignment
    X_train_df = pd.DataFrame(
        X_train_transformed_arr,
        columns=transformed_feature_names,
        index=train_df.index,
    )
    X_test_df = pd.DataFrame(
        X_test_transformed_arr,
        columns=transformed_feature_names,
        index=test_df.index,
    )

    # --------------------------------------------------------
    # 6. Comprehensive Post-Processing Validation Suite
    # --------------------------------------------------------
    print("\n[6/7] Running strict post-processing validation suite...", flush=True)

    # Check 1: Row counts
    if len(X_train_df) != n_train or len(X_test_df) != n_test:
        raise ValueError("Validation Failure: Transformed row count mismatch")
    if len(y_train) != n_train or len(y_test) != n_test:
        raise ValueError("Validation Failure: Target vector row count mismatch")
    if len(train_metadata) != n_train or len(test_metadata) != n_test:
        raise ValueError("Validation Failure: Metadata row count mismatch")

    # Check 2: Column alignment
    if list(X_train_df.columns) != list(X_test_df.columns):
        raise ValueError("Validation Failure: Train and test feature columns do not match in order or names")
    if len(set(X_train_df.columns)) != len(X_train_df.columns):
        raise ValueError("Validation Failure: Duplicate feature column names detected in transformed matrix")

    # Check 3: Aspect features present and raw aspect dropped
    if "aspect_degrees" in X_train_df.columns or "numeric__aspect_degrees" in X_train_df.columns:
        raise ValueError("Validation Failure: Raw 'aspect_degrees' was not dropped from feature matrix")
    if "numeric__aspect_sin" not in X_train_df.columns or "numeric__aspect_cos" not in X_train_df.columns:
        raise ValueError("Validation Failure: 'aspect_sin' or 'aspect_cos' missing from feature matrix")

    # Check 4: No missing values after preprocessing
    train_nans_after = int(X_train_df.isna().sum().sum())
    test_nans_after = int(X_test_df.isna().sum().sum())
    if train_nans_after > 0:
        raise ValueError(f"Validation Failure: {train_nans_after} missing values remain in X_train after preprocessing")
    if test_nans_after > 0:
        raise ValueError(f"Validation Failure: {test_nans_after} missing values remain in X_test after preprocessing")

    # Check 5: No infinite values after preprocessing
    train_infs = int(np.isinf(X_train_df.values).sum())
    test_infs = int(np.isinf(X_test_df.values).sum())
    if train_infs > 0:
        raise ValueError(f"Validation Failure: {train_infs} infinite values in X_train")
    if test_infs > 0:
        raise ValueError(f"Validation Failure: {test_infs} infinite values in X_test")

    # Check 6: One-hot encoded columns are strictly binary {0.0, 1.0}
    lulc_ohe_cols = [c for c in X_train_df.columns if "categorical__lulc_class" in c]
    for col in lulc_ohe_cols:
        unique_vals = set(X_train_df[col].unique()).union(set(X_test_df[col].unique()))
        if not unique_vals.issubset({0.0, 1.0}):
            raise ValueError(f"Validation Failure: OHE column '{col}' has non-binary values: {unique_vals}")

    # Check 7: Metadata coordinates and labels exactly match original master dataset
    master_lookup = df.set_index("sample_id")
    for meta_df, split_name in [(train_metadata, "train"), (test_metadata, "test")]:
        for row in meta_df.itertuples(index=False):
            sid = row.sample_id
            m_row = master_lookup.loc[sid]
            if abs(row.latitude - m_row["latitude"]) > 1e-7:
                raise ValueError(f"Validation Failure: Latitude mismatch for {sid} in {split_name} metadata")
            if abs(row.longitude - m_row["longitude"]) > 1e-7:
                raise ValueError(f"Validation Failure: Longitude mismatch for {sid} in {split_name} metadata")
            if row.landslide != m_row["landslide"]:
                raise ValueError(f"Validation Failure: Landslide label mismatch for {sid} in {split_name} metadata")

    # Check 8: Master dataset remained completely unmodified
    master_mtime_after = MASTER_DATASET_PATH.stat().st_mtime
    master_size_after = MASTER_DATASET_PATH.stat().st_size
    if (master_mtime_before != master_mtime_after) or (master_size_before != master_size_after):
        raise ValueError("CRITICAL ERROR: Master dataset file was modified during execution!")

    print("  All strict post-processing validation checks PASSED successfully.", flush=True)

    # --------------------------------------------------------
    # 7. Save Datasets and Preprocessing Artifacts
    # --------------------------------------------------------
    print("\n[7/7] Saving processed datasets and preprocessing pipeline artifacts...", flush=True)

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_PREPROCESSING_DIR.mkdir(parents=True, exist_ok=True)

    # Save split CSVs
    x_train_path = SPLITS_DIR / "X_train.csv"
    x_test_path = SPLITS_DIR / "X_test.csv"
    y_train_path = SPLITS_DIR / "y_train.csv"
    y_test_path = SPLITS_DIR / "y_test.csv"
    train_meta_path = SPLITS_DIR / "train_metadata.csv"
    test_meta_path = SPLITS_DIR / "test_metadata.csv"

    X_train_df.to_csv(x_train_path, index=False)
    X_test_df.to_csv(x_test_path, index=False)
    y_train.to_csv(y_train_path, index=False)
    y_test.to_csv(y_test_path, index=False)
    train_metadata.to_csv(train_meta_path, index=False)
    test_metadata.to_csv(test_meta_path, index=False)

    print(f"  -> Saved: {x_train_path}")
    print(f"  -> Saved: {x_test_path}")
    print(f"  -> Saved: {y_train_path}")
    print(f"  -> Saved: {y_test_path}")
    print(f"  -> Saved: {train_meta_path}")
    print(f"  -> Saved: {test_meta_path}")

    # Save fitted ColumnTransformer
    joblib.dump(preprocessor, PIPELINE_OUTPUT_PATH)
    print(f"  -> Saved pipeline: {PIPELINE_OUTPUT_PATH}")

    # Save feature manifest JSON
    feature_manifest = {
        "original_numeric_features": RAW_NUMERIC_FEATURES,
        "original_categorical_features": CATEGORICAL_FEATURES,
        "engineered_features": ENGINEERED_CIRCULAR_FEATURES,
        "final_numeric_features": FINAL_NUMERIC_FEATURES,
        "final_transformed_feature_names": transformed_feature_names,
        "total_transformed_features": n_features,
        "learned_lulc_categories": learned_lulc_categories,
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "train_samples": n_train,
        "test_samples": n_test,
    }
    with open(FEATURE_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_manifest, f, indent=4)
    print(f"  -> Saved feature manifest: {FEATURE_MANIFEST_PATH}")

    # --------------------------------------------------------
    # FINAL CONSOLE REPORT
    # --------------------------------------------------------
    elapsed = time.time() - start_time

    print("\n" + "=" * 80, flush=True)
    print("STEP 36 — ML PREPROCESSING REPORT", flush=True)
    print("=" * 80, flush=True)

    print("\n1. INPUT DATASET")
    print(f"  Master dataset rows:          {initial_row_count:,}")
    print(f"  Master dataset columns:       {initial_col_count}")
    print(f"  Original class distribution:  Positive={pos_count_init:,} (50.00%), Negative={neg_count_init:,} (50.00%)")

    print("\n2. TRAIN/TEST SPLIT")
    print(f"  Random state:                 {RANDOM_STATE}")
    print(f"  Test size:                    {TEST_SIZE:.2f} (20.0%)")
    print(f"  Training sample count:        {n_train:,} (80.0%)")
    print(f"  Testing sample count:         {n_test:,} (20.0%)")
    print(f"  Training class distribution:  Positive={train_pos:,} ({train_pos/n_train:.2%}), Negative={train_neg:,} ({train_neg/n_train:.2%})")
    print(f"  Testing class distribution:   Positive={test_pos:,} ({test_pos/n_test:.2%}), Negative={test_neg:,} ({test_neg/n_test:.2%})")

    print("\n3. MISSING VALUES BEFORE PREPROCESSING")
    print("  Feature                        Train Missing   Test Missing")
    print("  -------------------------------------------------------------")
    for feat in FINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        tr_m = int(train_missing_before.get(feat, 0))
        te_m = int(test_missing_before.get(feat, 0))
        if tr_m > 0 or te_m > 0:
            print(f"  {feat:<30s} {tr_m:>12d}   {te_m:>11d}")
    print("  -------------------------------------------------------------")
    print("  Missing values after preprocessing : 0")
    print("  Infinite values after preprocessing: 0")

    print("\n4. FEATURE ENGINEERING & TRANSFORMATION")
    print(f"  Original numeric features:    {len(RAW_NUMERIC_FEATURES)}")
    print("  Aspect transformation:        sin(rad) and cos(rad) engineered")
    print("  Raw aspect degrees:           DROPPED from ML feature matrix")
    print(f"  LULC categories from train:   {len(learned_lulc_categories)} categories ({learned_lulc_categories})")
    print(f"  Final transformed ML features:{n_features}")
    for idx, fname in enumerate(transformed_feature_names, start=1):
        print(f"    {idx:>2d}. {fname}")

    print("\n5. LEAKAGE VALIDATION")
    print("  Preprocessing fit status:     Fitted strictly on X_train ONLY")
    print("  Test transformation status:   X_test transformed using already-fitted pipeline")
    print("  Universal scaling:            None (deferred to model-specific pipelines)")

    print("\n6. CREATED ARTIFACTS")
    print(f"  1. {x_train_path}")
    print(f"  2. {x_test_path}")
    print(f"  3. {y_train_path}")
    print(f"  4. {y_test_path}")
    print(f"  5. {train_meta_path}")
    print(f"  6. {test_meta_path}")
    print(f"  7. {PIPELINE_OUTPUT_PATH}")
    print(f"  8. {FEATURE_MANIFEST_PATH}")

    print(f"\nExecution Time:                 {elapsed:.2f} seconds")
    print()
    print("Step 36 completed successfully.")
    print("ML preprocessing and train/test dataset preparation only.")
    print("Master dataset remains unchanged.")
    print("No machine learning model training was performed.")
    print("=" * 80 + "\n", flush=True)


if __name__ == "__main__":
    main()
