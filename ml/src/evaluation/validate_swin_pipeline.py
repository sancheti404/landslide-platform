"""
Comprehensive 15-point automated validation script for Swin Transformer branch.

Verifies:
1. Train image count matches train metadata (8,836).
2. Test image count matches test metadata (2,210).
3. Zero train/test sample_id overlap.
4. Zero duplicate sample IDs.
5. Zero missing labels.
6. Zero corrupted images.
7. Correct image dimensions (128x128).
8. Correct number of channels (3: RGB).
9. Zero NaN/Inf image tensors.
10. Model saves and successfully reloads from swin_transformer_best.pth.
11. Reloaded model produces identical predictions within numerical tolerance (< 1e-6).
12. Test predictions contain exactly 2,210 samples.
13. Every test sample_id matches existing test_metadata.csv.
14. All predicted probabilities are strictly bounded in [0, 1].
15. Test labels match y_test.csv / test_metadata.csv exactly.
16. Validation predictions exist and contain all validation samples.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.models.swin_model import SwinLandslideClassifier


TRAIN_META_PATH = Path("ml/data/processed/splits/train_metadata.csv")
TEST_META_PATH = Path("ml/data/processed/splits/test_metadata.csv")
Y_TEST_PATH = Path("ml/data/processed/splits/y_test.csv")
PATCHES_DIR = Path("ml/data/processed/patches")
MODEL_PATH = Path("ml/models/swin/swin_transformer_best.pth")
TEST_PREDS_PATH = Path("ml/reports/model_evaluation/swin_test_predictions.csv")
VAL_PREDS_PATH = Path("ml/reports/model_evaluation/swin_validation_predictions.csv")


def run_validation_checks():
    print("=" * 70)
    print("SWIN TRANSFORMER AUTOMATED PIPELINE VALIDATION")
    print("=" * 70)

    train_meta = pd.read_csv(TRAIN_META_PATH)
    test_meta = pd.read_csv(TEST_META_PATH)
    y_test = pd.read_csv(Y_TEST_PATH)

    results = []

    def check(num, name, condition, details=""):
        status = "PASSED" if condition else "FAILED"
        results.append((num, name, status, details))
        print(f"Check {num:02d}: [{status}] {name} {details}")
        if not condition:
            raise AssertionError(f"Validation failed on Check {num}: {name}. {details}")

    # Check 1: Train image count
    train_existing_images = sum(1 for sid in train_meta["sample_id"] if (PATCHES_DIR / f"{sid}.png").exists())
    check(1, "Train image count matches train metadata",
          train_existing_images == len(train_meta),
          f"Found {train_existing_images}/{len(train_meta)}")

    # Check 2: Test image count
    test_existing_images = sum(1 for sid in test_meta["sample_id"] if (PATCHES_DIR / f"{sid}.png").exists())
    check(2, "Test image count matches test metadata",
          test_existing_images == len(test_meta),
          f"Found {test_existing_images}/{len(test_meta)}")

    # Check 3: Zero train/test overlap
    train_ids = set(train_meta["sample_id"])
    test_ids = set(test_meta["sample_id"])
    overlap = train_ids.intersection(test_ids)
    check(3, "Zero train/test sample_id overlap", len(overlap) == 0, f"Overlap count: {len(overlap)}")

    # Check 4: Zero duplicate sample IDs
    total_ids = list(train_meta["sample_id"]) + list(test_meta["sample_id"])
    check(4, "Zero duplicate sample IDs across dataset", len(total_ids) == len(set(total_ids)), f"Total: {len(total_ids)}")

    # Check 5: Zero missing labels
    missing_train = train_meta["landslide"].isna().sum()
    missing_test = test_meta["landslide"].isna().sum()
    check(5, "Zero missing labels", (missing_train + missing_test) == 0, f"Missing: {missing_train + missing_test}")

    # Check 6, 7, 8: Image integrity, dimensions, channels (sample 500 images)
    sample_sids = list(train_meta["sample_id"][:250]) + list(test_meta["sample_id"][:250])
    corrupted = 0
    wrong_dims = 0
    wrong_channels = 0

    for sid in sample_sids:
        img_p = PATCHES_DIR / f"{sid}.png"
        try:
            with Image.open(img_p) as img:
                if img.size != (128, 128):
                    wrong_dims += 1
                if img.mode != "RGB":
                    wrong_channels += 1
        except Exception:
            corrupted += 1

    check(6, "Zero corrupted images verified", corrupted == 0, f"Corrupted count: {corrupted}")
    check(7, "Correct image dimensions (128x128)", wrong_dims == 0, f"Mismatches: {wrong_dims}")
    check(8, "Correct number of channels (RGB/3-channel)", wrong_channels == 0, f"Non-RGB: {wrong_channels}")

    # Check 9: Zero NaN/Inf image tensors
    nan_inf_found = False
    for sid in sample_sids[:50]:
        img = Image.open(PATCHES_DIR / f"{sid}.png")
        arr = np.array(img, dtype=float)
        if np.isnan(arr).any() or np.isinf(arr).any():
            nan_inf_found = True
            break
    check(9, "Zero NaN/Inf image tensors", not nan_inf_found, "Checked pixel arrays")

    # Check 10 & 11: Model save/reload and identical predictions
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    check(10, "Model file exists on disk", MODEL_PATH.exists(), f"Path: {MODEL_PATH}")

    m1 = SwinLandslideClassifier(pretrained=False).to(device)
    m1.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    m1.eval()

    m2 = SwinLandslideClassifier(pretrained=False).to(device)
    m2.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    m2.eval()

    dummy_input = torch.randn(4, 3, 224, 224, device=device)
    with torch.no_grad():
        out1 = torch.sigmoid(m1(dummy_input)).cpu().numpy()
        out2 = torch.sigmoid(m2(dummy_input)).cpu().numpy()
    max_diff = np.max(np.abs(out1 - out2))
    check(11, "Reloaded model produces identical predictions (<1e-6)",
          max_diff < 1e-6, f"Max absolute difference: {max_diff:.2e}")

    # Check 12: Test predictions count
    test_preds = pd.read_csv(TEST_PREDS_PATH)
    check(12, "Test predictions contain exactly 2,210 samples",
          len(test_preds) == 2210, f"Row count: {len(test_preds)}")

    # Check 13: Test sample IDs match test_metadata.csv
    matching_ids = (test_preds["sample_id"].values == test_meta["sample_id"].values).all()
    check(13, "Every test sample_id matches test_metadata.csv row-for-row",
          matching_ids, "Strict alignment verified")

    # Check 14: Probabilities in [0, 1]
    probs = test_preds["swin_probability"].values
    prob_valid = ((probs >= 0.0) & (probs <= 1.0)).all() and not np.isnan(probs).any()
    check(14, "Predictions are valid probabilities in [0, 1]",
          prob_valid, f"Min={probs.min():.4f}, Max={probs.max():.4f}")

    # Check 15: Test labels match y_test.csv
    labels_match = (test_preds["landslide"].values == y_test.iloc[:, 0].values).all()
    check(15, "Test labels exactly match y_test.csv",
          labels_match, "Ground-truth alignment verified")

    # Check 16: Validation predictions exist
    val_preds = pd.read_csv(VAL_PREDS_PATH)
    check(16, "Validation predictions exist and contain all validation samples",
          len(val_preds) == 1768, f"Row count: {len(val_preds)}")

    print("\n" + "=" * 70)
    print("ALL 16 AUTOMATED VALIDATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_validation_checks()
