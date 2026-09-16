"""
Held-out test set evaluation for Swin Transformer satellite visual risk branch.

Strict Quarantined Protocol:
- Evaluates exactly ONCE on the held-out 2,210-sample test set.
- Calculates Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Specificity, FPR, FNR, Confusion Matrix.
- Generates swin_test_predictions.csv, swin_test_metrics.csv, and evaluation curves.
- Verifies model reload reproducibility.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.data.swin_dataset import create_dataloaders
from src.models.swin_model import SwinLandslideClassifier


TEST_META_PATH = Path("ml/data/processed/splits/test_metadata.csv")
PATCHES_DIR = Path("ml/data/processed/patches")
MODEL_PATH = Path("ml/models/swin/swin_transformer_best.pth")
REPORTS_DIR = Path("ml/reports/model_evaluation")
FIGURES_DIR = Path("ml/reports/figures")


def evaluate_swin_test_set():
    print("=" * 70)
    print("STEP 39: SWIN TRANSFORMER HELD-OUT TEST SET EVALUATION")
    print("=" * 70)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load test metadata
    test_meta = pd.read_csv(TEST_META_PATH)
    print(f"Loaded held-out test metadata: {len(test_meta)} samples.")

    # Create test loader
    _, _, test_loader = create_dataloaders(
        train_df=test_meta,  # dummy placeholder
        val_df=test_meta,    # dummy placeholder
        test_df=test_meta,
        patches_dir=PATCHES_DIR,
        batch_size=32,
        num_workers=0,
        image_size=224
    )

    # 2. Load model
    print(f"Loading trained weights from {MODEL_PATH}...")
    model = SwinLandslideClassifier(pretrained=False, dropout_rate=0.3).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    all_sample_ids = []
    all_lats = []
    all_lons = []
    all_targets = []
    all_probs = []

    print("Running single evaluation pass on held-out test set...")
    with torch.no_grad():
        for batch in test_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            sample_ids = batch["sample_id"]
            lats = batch["latitude"].numpy()
            lons = batch["longitude"].numpy()

            logits = model(images).squeeze(-1)
            probs = torch.sigmoid(logits).cpu().numpy()

            all_sample_ids.extend(sample_ids)
            all_lats.extend(lats)
            all_lons.extend(lons)
            all_targets.extend(labels.cpu().numpy())
            all_probs.extend(probs)

    y_true = np.array(all_targets, dtype=int)
    y_prob = np.array(all_probs, dtype=float)
    y_pred = (y_prob >= 0.5).astype(int)

    # 3. Calculate metrics
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    print("\n" + "=" * 50)
    print("HELD-OUT TEST SET PERFORMANCE METRICS")
    print("=" * 50)
    print(f"Accuracy:    {accuracy:.4f}")
    print(f"Precision:   {precision:.4f}")
    print(f"Recall:      {recall:.4f}")
    print(f"F1-Score:    {f1:.4f}")
    print(f"ROC-AUC:     {roc_auc:.4f}")
    print(f"PR-AUC:      {pr_auc:.4f}")
    print(f"Specificity: {specificity:.4f}")
    print(f"FPR:         {fpr:.4f}")
    print(f"FNR:         {fnr:.4f}")
    print(f"\nConfusion Matrix:\nTN={tn}, FP={fp}\nFN={fn}, TP={tp}")
    print("=" * 50)

    # Save metrics CSV
    metrics_dict = {
        "metric": [
            "accuracy", "precision", "recall", "f1_score",
            "roc_auc", "pr_auc", "specificity", "fpr", "fnr",
            "true_negatives", "false_positives", "false_negatives", "true_positives",
            "test_samples"
        ],
        "value": [
            round(accuracy, 4), round(precision, 4), round(recall, 4), round(f1, 4),
            round(roc_auc, 4), round(pr_auc, 4), round(specificity, 4), round(fpr, 4), round(fnr, 4),
            int(tn), int(fp), int(fn), int(tp),
            len(y_true)
        ]
    }
    metrics_df = pd.DataFrame(metrics_dict)
    metrics_path = REPORTS_DIR / "swin_test_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"\nSaved test metrics to {metrics_path}")

    # 4. Save critical test predictions CSV
    predictions_df = pd.DataFrame({
        "sample_id": all_sample_ids,
        "latitude": all_lats,
        "longitude": all_lons,
        "landslide": y_true,
        "swin_probability": y_prob,
        "swin_prediction": y_pred
    })
    preds_path = REPORTS_DIR / "swin_test_predictions.csv"
    predictions_df.to_csv(preds_path, index=False)
    print(f"Saved test predictions to {preds_path} ({len(predictions_df)} samples)")

    # 5. Visualizations
    # A. Confusion Matrix
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Non-Landslide (0)", "Landslide (1)"])
    disp.plot(cmap="Blues", ax=ax, colorbar=False)
    plt.title("Swin Transformer - Held-out Test Confusion Matrix", fontsize=12, fontweight="bold")
    plt.tight_layout()
    cm_path = FIGURES_DIR / "swin_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()

    # B. ROC Curve
    fpr_curve, tpr_curve, _ = roc_curve(y_true, y_prob)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr_curve, tpr_curve, color="#1f77b4", lw=2, label=f"Swin-T (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="gray", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.5000)")
    plt.title("Swin Transformer - Held-out Test ROC Curve", fontsize=13, fontweight="bold")
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    plt.ylabel("True Positive Rate (Recall)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()
    roc_path = FIGURES_DIR / "swin_roc_curve.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()

    # C. Precision-Recall Curve
    prec_curve, rec_curve, _ = precision_recall_curve(y_true, y_prob)
    plt.figure(figsize=(7, 6))
    plt.plot(rec_curve, prec_curve, color="#2ca02c", lw=2, label=f"Swin-T (PR-AUC = {pr_auc:.4f})")
    plt.axhline(y=0.5, color="gray", lw=1.5, linestyle="--", label="Baseline (0.5000)")
    plt.title("Swin Transformer - Held-out Test Precision-Recall Curve", fontsize=13, fontweight="bold")
    plt.xlabel("Recall", fontsize=11)
    plt.ylabel("Precision", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower left", fontsize=11)
    plt.tight_layout()
    pr_path = FIGURES_DIR / "swin_precision_recall_curve.png"
    plt.savefig(pr_path, dpi=300)
    plt.close()

    print(f"Saved evaluation figures:\n  {cm_path}\n  {roc_path}\n  {pr_path}")

    # 6. Verify Model Reload Reproducibility
    print("\nVerifying model save/reload prediction reproducibility...")
    reloaded_model = SwinLandslideClassifier(pretrained=False, dropout_rate=0.3).to(device)
    reloaded_model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    reloaded_model.eval()

    sample_batch = next(iter(test_loader))
    sample_imgs = sample_batch["image"].to(device)

    with torch.no_grad():
        orig_out = torch.sigmoid(model(sample_imgs)).cpu().numpy()
        reloaded_out = torch.sigmoid(reloaded_model(sample_imgs)).cpu().numpy()

    max_diff = np.max(np.abs(orig_out - reloaded_out))
    print(f"Max prediction difference between original and reloaded model: {max_diff:.2e}")
    assert max_diff < 1e-6, f"Reloaded model outputs differ by {max_diff}!"
    print("Model reload reproducibility check passed successfully!")


if __name__ == "__main__":
    evaluate_swin_test_set()
