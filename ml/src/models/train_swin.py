"""
Training pipeline for Swin Transformer satellite visual risk branch.

Enforces strict leakage safety:
- Splits train_metadata.csv (8,836 samples) into Train (7,068) and Validation (1,768) (80/20 stratified, seed=42).
- Zero access to test_metadata.csv during training or model selection.
- Phased transfer learning: head training then controlled fine-tuning.
- Early stopping based strictly on Validation ROC-AUC.
- Generates swin_transformer_best.pth, swin_training_history.csv, and swin_validation_predictions.csv.
"""

import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import matplotlib.pyplot as plt

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.data.swin_dataset import create_dataloaders
from src.models.swin_model import SwinLandslideClassifier


TRAIN_META_PATH = Path("ml/data/processed/splits/train_metadata.csv")
TEST_META_PATH = Path("ml/data/processed/splits/test_metadata.csv")
PATCHES_DIR = Path("ml/data/processed/patches")
MODEL_DIR = Path("ml/models/swin")
REPORTS_DIR = Path("ml/reports/model_evaluation")
FIGURES_DIR = Path("ml/reports/figures")

SEED = 42
BATCH_SIZE = 16
IMAGE_SIZE = 224
PHASE1_EPOCHS = 3
PHASE2_EPOCHS = 10
EARLY_STOP_PATIENCE = 3


def set_seed(seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True


def evaluate_loader(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_targets = []
    all_probs = []
    all_sample_ids = []
    all_lats = []
    all_lons = []

    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            sample_ids = batch["sample_id"]
            lats = batch["latitude"].numpy()
            lons = batch["longitude"].numpy()

            logits = model(images).squeeze(-1)
            loss = criterion(logits, labels)
            probs = torch.sigmoid(logits).cpu().numpy()

            total_loss += loss.item() * len(labels)
            all_targets.extend(labels.cpu().numpy())
            all_probs.extend(probs)
            all_sample_ids.extend(sample_ids)
            all_lats.extend(lats)
            all_lons.extend(lons)

    avg_loss = total_loss / len(loader.dataset)
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)
    preds = (all_probs >= 0.5).astype(int)

    auc = roc_auc_score(all_targets, all_probs)
    acc = accuracy_score(all_targets, preds)

    metrics = {
        "loss": avg_loss,
        "roc_auc": auc,
        "accuracy": acc,
        "targets": all_targets,
        "probs": all_probs,
        "sample_ids": all_sample_ids,
        "lats": all_lats,
        "lons": all_lons,
    }
    return metrics


def train_swin_pipeline():
    print("=" * 70)
    print("STEP 39: SWIN TRANSFORMER TRAINING PIPELINE")
    print("=" * 70)

    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load train metadata and create stratified train/val split
    train_meta_full = pd.read_csv(TRAIN_META_PATH)
    test_meta = pd.read_csv(TEST_META_PATH)

    train_df, val_df = train_test_split(
        train_meta_full,
        test_size=0.20,
        random_state=SEED,
        stratify=train_meta_full["landslide"]
    )

    print(f"Dataset partitioning:")
    print(f"  Training samples:   {len(train_df)} (Pos: {train_df['landslide'].sum()}, Neg: {len(train_df)-train_df['landslide'].sum()})")
    print(f"  Validation samples: {len(val_df)} (Pos: {val_df['landslide'].sum()}, Neg: {len(val_df)-val_df['landslide'].sum()})")
    print(f"  Held-out Test:      {len(test_meta)} (Quarantined)")

    train_loader, val_loader, _ = create_dataloaders(
        train_df=train_df,
        val_df=val_df,
        test_df=test_meta,
        patches_dir=PATCHES_DIR,
        batch_size=BATCH_SIZE,
        num_workers=0,
        image_size=IMAGE_SIZE
    )

    # 2. Instantiate Swin model
    model = SwinLandslideClassifier(pretrained=True, dropout_rate=0.3).to(device)
    criterion = nn.BCEWithLogitsLoss()

    history = []
    best_val_auc = 0.0
    best_model_path = MODEL_DIR / "swin_transformer_best.pth"
    patience_counter = 0

    # -------------------------------------------------------------
    # PHASE 1: Train classification head with frozen backbone
    # -------------------------------------------------------------
    print("\n--- PHASE 1: Training Classification Head (Backbone Frozen) ---")
    model.freeze_backbone()
    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3, weight_decay=1e-4)
    scaler = torch.amp.GradScaler('cuda', enabled=(device.type == "cuda"))

    for epoch in range(1, PHASE1_EPOCHS + 1):
        model.train()
        train_loss = 0.0
        t0 = time.time()

        for batch in train_loader:
            images = batch["image"].to(device, non_blocking=True)
            labels = batch["label"].to(device, non_blocking=True)

            optimizer.zero_grad()
            with torch.amp.autocast('cuda', enabled=(device.type == "cuda")):
                logits = model(images).squeeze(-1)
                loss = criterion(logits, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item() * len(labels)

        avg_train_loss = train_loss / len(train_loader.dataset)
        val_metrics = evaluate_loader(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        print(f"Epoch {epoch:02d}/{PHASE1_EPOCHS} [Phase 1] - {elapsed:.1f}s | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Val Loss: {val_metrics['loss']:.4f} | "
              f"Val Acc: {val_metrics['accuracy']:.4f} | "
              f"Val AUC: {val_metrics['roc_auc']:.4f}")

        history.append({
            "epoch": epoch,
            "phase": "Phase 1 (Head)",
            "train_loss": avg_train_loss,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_roc_auc": val_metrics["roc_auc"],
            "lr": 1e-3
        })

        if val_metrics["roc_auc"] > best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            torch.save(model.state_dict(), best_model_path)
            print(f"  --> Saved new best model checkpoint (Val AUC: {best_val_auc:.4f})")

    # -------------------------------------------------------------
    # PHASE 2: Controlled Fine-Tuning of Later Stages
    # -------------------------------------------------------------
    print("\n--- PHASE 2: Fine-Tuning Later Stages with Cosine Annealing ---")
    model.unfreeze_later_stages()
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Trainable parameters in Phase 2: {trainable_params:,} / {total_params:,} ({100*trainable_params/total_params:.1f}%)")

    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=5e-5, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=PHASE2_EPOCHS, eta_min=1e-6)

    for epoch_idx in range(1, PHASE2_EPOCHS + 1):
        global_epoch = PHASE1_EPOCHS + epoch_idx
        model.train()
        train_loss = 0.0
        t0 = time.time()

        for batch in train_loader:
            images = batch["image"].to(device, non_blocking=True)
            labels = batch["label"].to(device, non_blocking=True)

            optimizer.zero_grad()
            with torch.amp.autocast('cuda', enabled=(device.type == "cuda")):
                logits = model(images).squeeze(-1)
                loss = criterion(logits, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item() * len(labels)

        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]
        avg_train_loss = train_loss / len(train_loader.dataset)
        val_metrics = evaluate_loader(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        print(f"Epoch {global_epoch:02d}/{PHASE1_EPOCHS + PHASE2_EPOCHS} [Phase 2] - {elapsed:.1f}s | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Val Loss: {val_metrics['loss']:.4f} | "
              f"Val Acc: {val_metrics['accuracy']:.4f} | "
              f"Val AUC: {val_metrics['roc_auc']:.4f} | "
              f"LR: {current_lr:.2e}")

        history.append({
            "epoch": global_epoch,
            "phase": "Phase 2 (Fine-tuning)",
            "train_loss": avg_train_loss,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_roc_auc": val_metrics["roc_auc"],
            "lr": current_lr
        })

        if val_metrics["roc_auc"] > best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            torch.save(model.state_dict(), best_model_path)
            patience_counter = 0
            print(f"  --> Saved new best model checkpoint (Val AUC: {best_val_auc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOP_PATIENCE:
                print(f"Early stopping triggered at epoch {global_epoch} (patience={EARLY_STOP_PATIENCE})")
                break

    # 3. Save training history
    history_df = pd.DataFrame(history)
    history_path = REPORTS_DIR / "swin_training_history.csv"
    history_df.to_csv(history_path, index=False)
    print(f"\nSaved training history to {history_path}")

    # Plot training history curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(history_df["epoch"], history_df["train_loss"], label="Train Loss", marker="o")
    ax1.plot(history_df["epoch"], history_df["val_loss"], label="Validation Loss", marker="s")
    ax1.set_title("Training and Validation Loss", fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Binary Cross Entropy Loss")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    ax2.plot(history_df["epoch"], history_df["val_roc_auc"], label="Val ROC-AUC", color="green", marker="^")
    ax2.plot(history_df["epoch"], history_df["val_accuracy"], label="Val Accuracy", color="orange", marker="d")
    ax2.set_title("Validation ROC-AUC & Accuracy", fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Score")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    training_fig_path = FIGURES_DIR / "swin_training_history.png"
    plt.savefig(training_fig_path, dpi=300)
    plt.close()
    print(f"Saved training curves to {training_fig_path}")

    # 4. Reload best model and generate validation predictions (Req 16)
    print(f"\nReloading best model from {best_model_path} for validation prediction export...")
    model.load_state_dict(torch.load(best_model_path, map_location=device))
    val_final_metrics = evaluate_loader(model, val_loader, criterion, device)

    val_preds_df = pd.DataFrame({
        "sample_id": val_final_metrics["sample_ids"],
        "latitude": val_final_metrics["lats"],
        "longitude": val_final_metrics["lons"],
        "landslide": val_final_metrics["targets"].astype(int),
        "swin_probability": val_final_metrics["probs"],
        "swin_prediction": (val_final_metrics["probs"] >= 0.5).astype(int)
    })

    val_pred_path = REPORTS_DIR / "swin_validation_predictions.csv"
    val_preds_df.to_csv(val_pred_path, index=False)
    print(f"Saved validation predictions to {val_pred_path} ({len(val_preds_df)} samples, Val AUC={val_final_metrics['roc_auc']:.4f})")

    # 5. Save model configuration and label mapping
    config = {
        "model_architecture": "Swin-Tiny (swin_t)",
        "pretrained": True,
        "input_channels": 3,
        "bands": ["B4", "B3", "B2"],
        "patch_size_pixels": [128, 128],
        "input_tensor_resolution": [224, 224],
        "ground_footprint_meters": 1280.0,
        "spatial_resolution_meters": 10.0,
        "dataset_source": "COPERNICUS/S2_SR_HARMONIZED",
        "composite_method": "Temporal Median 2023 with SCL cloud mask",
        "dropout_rate": 0.3,
        "best_val_roc_auc": round(float(val_final_metrics["roc_auc"]), 4),
        "best_val_accuracy": round(float(val_final_metrics["accuracy"]), 4),
        "seed": SEED
    }
    with open(MODEL_DIR / "swin_transformer_config.json", "w") as f:
        json.dump(config, f, indent=4)

    label_mapping = {"0": "non_landslide", "1": "landslide"}
    with open(MODEL_DIR / "swin_label_mapping.json", "w") as f:
        json.dump(label_mapping, f, indent=4)

    print("Model configuration and label mapping saved successfully.")


if __name__ == "__main__":
    train_swin_pipeline()
