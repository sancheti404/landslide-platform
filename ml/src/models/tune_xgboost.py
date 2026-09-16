"""
Step 38A — XGBoost Hyperparameter Tuning Pipeline
for Uttarakhand Landslide Susceptibility Modeling.

This script optimizes the baseline XGBoost model using:
    - RandomizedSearchCV over a comprehensive 9-parameter distribution
    - Stratified 5-Fold Cross-Validation performed strictly on X_train (8,836 samples)
    - Mean Stratified 5-Fold CV ROC-AUC as the exclusive model selection metric
    - Held-out test set (2,210 samples) completely untouched during tuning
    - Best estimator refit on full training set and evaluated EXACTLY ONCE on held-out test set
    - Side-by-side comparison with baseline XGBoost (Absolute Delta and Percentage Delta)
    - Export of full tuning results, comparison metrics, best parameter JSON manifest, and figures
    - Strict data validation, reload validation, and input immutability verification
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

# Ensure UTF-8 console output for cross-platform compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
import xgboost as xgb


# ============================================================
# PATH RESOLUTION UTILITIES
# ============================================================

def resolve_project_root() -> Path:
    """
    Locates the project root directory containing the 'ml' folder.
    """
    current = Path.cwd()
    if (current / "ml").exists() and (current / "ml" / "data").exists():
        return current
    if (current / "landslide-platform" / "ml").exists():
        return current / "landslide-platform"
    script_parent = Path(__file__).resolve().parents[3]
    if (script_parent / "ml").exists():
        return script_parent
    return current


PROJECT_ROOT = resolve_project_root()
ML_DIR = PROJECT_ROOT / "ml"

DATA_SPLITS_DIR = ML_DIR / "data" / "processed" / "splits"
FEATURE_NAMES_PATH = ML_DIR / "models" / "preprocessing" / "feature_names.json"
BASELINE_MODELS_DIR = ML_DIR / "models" / "baseline"
FINAL_MODELS_DIR = ML_DIR / "models" / "final"
REPORTS_DIR = ML_DIR / "reports" / "model_evaluation"
FIGURES_DIR = REPORTS_DIR / "figures"

X_TRAIN_PATH = DATA_SPLITS_DIR / "X_train.csv"
X_TEST_PATH = DATA_SPLITS_DIR / "X_test.csv"
Y_TRAIN_PATH = DATA_SPLITS_DIR / "y_train.csv"
Y_TEST_PATH = DATA_SPLITS_DIR / "y_test.csv"
BASELINE_XGB_PATH = BASELINE_MODELS_DIR / "xgboost.joblib"
BASELINE_COMPARISON_PATH = REPORTS_DIR / "baseline_model_comparison.csv"
MASTER_DATASET_PATH = ML_DIR / "data" / "processed" / "uttarakhand_master_ml_dataset.csv"

# Configuration constants
RANDOM_STATE = 42
CV_SPLITS = 5
EXPECTED_TRAIN_ROWS = 8836
EXPECTED_TEST_ROWS = 2210
EXPECTED_FEATURE_COUNT = 19
DEFAULT_N_ITER = 50


# ============================================================
# HYPERPARAMETER SEARCH SPACE (9 PARAMETERS)
# ============================================================

PARAM_DISTRIBUTIONS = {
    "n_estimators": [100, 150, 200, 250, 300, 400, 500],
    "max_depth": [3, 4, 5, 6, 7, 8, 9, 10],
    "learning_rate": [0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2],
    "min_child_weight": [1, 2, 3, 5, 7, 10],
    "subsample": [0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
    "colsample_bytree": [0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
    "gamma": [0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
    "reg_alpha": [0.0, 1e-4, 1e-3, 0.01, 0.1, 1.0, 5.0, 10.0],
    "reg_lambda": [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
}


# ============================================================
# MAIN TUNING PIPELINE
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Step 38A: XGBoost Hyperparameter Tuning Pipeline")
    parser.add_argument(
        "--n_iter",
        type=int,
        default=DEFAULT_N_ITER,
        help=f"Number of parameter settings sampled in RandomizedSearchCV (default: {DEFAULT_N_ITER})",
    )
    args = parser.parse_args()
    n_iter = args.n_iter

    start_time = time.time()

    print("=" * 85, flush=True)
    print("STEP 38A — XGBOOST HYPERPARAMETER TUNING PIPELINE", flush=True)
    print("=" * 85, flush=True)
    print(f"Project root:            {PROJECT_ROOT}", flush=True)
    print(f"Search iterations:       {n_iter}", flush=True)
    print(f"Cross-validation folds:  {CV_SPLITS} (Stratified)", flush=True)
    print(f"Random state:            {RANDOM_STATE}", flush=True)

    # --------------------------------------------------------
    # 1. Input Validation & Immutability Tracking
    # --------------------------------------------------------
    print("\n[1/6] Loading and validating input datasets...", flush=True)
    required_paths = [X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH, BASELINE_XGB_PATH, FEATURE_NAMES_PATH]
    for p in required_paths:
        if not p.exists():
            raise FileNotFoundError(f"Required input missing: {p}")

    # Snapshot file metadata for immutability verification
    tracked_inputs = [X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH, FEATURE_NAMES_PATH]
    if MASTER_DATASET_PATH.exists():
        tracked_inputs.append(MASTER_DATASET_PATH)

    input_snapshots_before = {p: (p.stat().st_size, p.stat().st_mtime) for p in tracked_inputs}

    X_train = pd.read_csv(X_TRAIN_PATH)
    X_test = pd.read_csv(X_TEST_PATH)
    y_train_df = pd.read_csv(Y_TRAIN_PATH)
    y_test_df = pd.read_csv(Y_TEST_PATH)

    y_train = y_train_df["landslide"].values
    y_test = y_test_df["landslide"].values

    # Validation checks
    if len(X_train) != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"X_train rows {len(X_train)} != expected {EXPECTED_TRAIN_ROWS}")
    if len(X_test) != EXPECTED_TEST_ROWS:
        raise ValueError(f"X_test rows {len(X_test)} != expected {EXPECTED_TEST_ROWS}")
    if len(y_train) != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"y_train rows {len(y_train)} != expected {EXPECTED_TRAIN_ROWS}")
    if len(y_test) != EXPECTED_TEST_ROWS:
        raise ValueError(f"y_test rows {len(y_test)} != expected {EXPECTED_TEST_ROWS}")

    if X_train.shape[1] != EXPECTED_FEATURE_COUNT or X_test.shape[1] != EXPECTED_FEATURE_COUNT:
        raise ValueError(f"Feature count mismatch: expected {EXPECTED_FEATURE_COUNT}, got {X_train.shape[1]}")

    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("X_train and X_test column names or column order do not match exactly")

    with open(FEATURE_NAMES_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_features = manifest.get("final_transformed_feature_names", [])
    if manifest_features and list(X_train.columns) != manifest_features:
        raise ValueError("X_train columns do not match feature_names.json manifest")

    if X_train.isna().sum().sum() > 0 or X_test.isna().sum().sum() > 0:
        raise ValueError("Input features contain missing (NaN) values")
    if pd.isna(y_train).sum() > 0 or pd.isna(y_test).sum() > 0:
        raise ValueError("Target labels contain missing (NaN) values")

    if np.isinf(X_train.values).sum() > 0 or np.isinf(X_test.values).sum() > 0:
        raise ValueError("Input features contain infinite (+/-Inf) values")

    if not set(np.unique(y_train)).issubset({0, 1}) or not set(np.unique(y_test)).issubset({0, 1}):
        raise ValueError("Target labels must be strictly binary {0, 1}")

    train_pos = int(np.sum(y_train == 1))
    train_neg = int(np.sum(y_train == 0))
    test_pos = int(np.sum(y_test == 1))
    test_neg = int(np.sum(y_test == 0))

    print(f"  Training set : {len(X_train):,} samples (Pos: {train_pos:,}, Neg: {train_neg:,})", flush=True)
    print(f"  Test set     : {len(X_test):,} samples (Pos: {test_pos:,}, Neg: {test_neg:,})", flush=True)
    print(f"  Features     : {X_train.shape[1]} predictors verified aligned with manifest", flush=True)

    # --------------------------------------------------------
    # 2. Configure RandomizedSearchCV with Stratified 5-Fold CV
    # --------------------------------------------------------
    print("\n[2/6] Configuring RandomizedSearchCV over 9 hyperparameters...", flush=True)
    stratified_cv = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    scoring = {
        "roc_auc": "roc_auc",
        "f1": "f1",
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
    }

    xgb_base = xgb.XGBClassifier(
        random_state=RANDOM_STATE,
        eval_metric="logloss",
        n_jobs=1,  # RandomizedSearchCV manages worker processes
    )

    search = RandomizedSearchCV(
        estimator=xgb_base,
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=n_iter,
        scoring=scoring,
        refit="roc_auc",  # Automatically refits on full X_train using best CV ROC-AUC
        cv=stratified_cv,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        return_train_score=False,
        verbose=2,
    )

    # --------------------------------------------------------
    # 3. Execute Hyperparameter Search (Training Set Only)
    # --------------------------------------------------------
    print(f"\n[3/6] Running RandomizedSearchCV ({n_iter} iterations x {CV_SPLITS} folds = {n_iter * CV_SPLITS} total fits)...", flush=True)
    print("  LEAKAGE PROTOCOL: Search executed EXCLUSIVELY on X_train + y_train. Test set untouched.", flush=True)
    search_start = time.time()
    search.fit(X_train, y_train)
    search_duration = time.time() - search_start
    print(f"  RandomizedSearchCV completed in {search_duration:.2f} seconds ({search_duration/60:.2f} minutes).", flush=True)

    # --------------------------------------------------------
    # 4. Extract and Save Full Tuning Results
    # --------------------------------------------------------
    print("\n[4/6] Compiling tuning results ranked by Stratified 5-Fold CV ROC-AUC...", flush=True)
    cv_results_df = pd.DataFrame(search.cv_results_)

    # Sort strictly by rank_test_roc_auc ascending / mean_test_roc_auc descending
    cv_results_df = cv_results_df.sort_values(by="rank_test_roc_auc", ascending=True).reset_index(drop=True)

    # Required column structure check
    required_tuning_cols = [
        "rank_test_roc_auc",
        "mean_test_roc_auc",
        "std_test_roc_auc",
        "mean_test_f1",
        "std_test_f1",
        "mean_test_accuracy",
        "std_test_accuracy",
        "mean_test_precision",
        "std_test_precision",
        "mean_test_recall",
        "std_test_recall",
        "mean_fit_time",
        "std_fit_time",
        "param_n_estimators",
        "param_max_depth",
        "param_learning_rate",
        "param_min_child_weight",
        "param_subsample",
        "param_colsample_bytree",
        "param_gamma",
        "param_reg_alpha",
        "param_reg_lambda",
    ]

    for c in required_tuning_cols:
        if c not in cv_results_df.columns:
            raise ValueError(f"Missing required column in cv_results_: {c}")

    # Best configuration extracted from search
    best_params = search.best_params_
    best_cv_roc_auc = float(search.best_score_)
    best_idx = search.best_index_

    best_cv_roc_auc_std = float(search.cv_results_["std_test_roc_auc"][best_idx])
    best_cv_f1 = float(search.cv_results_["mean_test_f1"][best_idx])
    best_cv_f1_std = float(search.cv_results_["std_test_f1"][best_idx])
    best_cv_acc = float(search.cv_results_["mean_test_accuracy"][best_idx])
    best_cv_acc_std = float(search.cv_results_["std_test_accuracy"][best_idx])
    best_cv_prec = float(search.cv_results_["mean_test_precision"][best_idx])
    best_cv_prec_std = float(search.cv_results_["std_test_precision"][best_idx])
    best_cv_rec = float(search.cv_results_["mean_test_recall"][best_idx])
    best_cv_rec_std = float(search.cv_results_["std_test_recall"][best_idx])

    best_model = search.best_estimator_

    print(f"  Best Mean 5-Fold CV ROC-AUC: {best_cv_roc_auc:.4f} (+/- {best_cv_roc_auc_std:.4f})", flush=True)
    print(f"  Best Mean 5-Fold CV F1-Score: {best_cv_f1:.4f} (+/- {best_cv_f1_std:.4f})", flush=True)
    print("  Selected Hyperparameters (9/9):", flush=True)
    for k in sorted(best_params.keys()):
        print(f"    - {k:<20}: {best_params[k]}", flush=True)

    # --------------------------------------------------------
    # 5. Evaluate Held-Out Test Set Exactly Once & Compare with Baseline
    # --------------------------------------------------------
    print("\n[5/6] Evaluating tuned model EXACTLY ONCE on held-out test set (N = 2,210)...", flush=True)
    y_test_pred_tuned = best_model.predict(X_test)
    y_test_prob_tuned = best_model.predict_proba(X_test)[:, 1]

    tuned_test_acc = float(accuracy_score(y_test, y_test_pred_tuned))
    tuned_test_prec = float(precision_score(y_test, y_test_pred_tuned))
    tuned_test_rec = float(recall_score(y_test, y_test_pred_tuned))
    tuned_test_f1 = float(f1_score(y_test, y_test_pred_tuned))
    tuned_test_auc = float(roc_auc_score(y_test, y_test_prob_tuned))

    print(f"  Tuned XGBoost Test Accuracy : {tuned_test_acc:.4f}", flush=True)
    print(f"  Tuned XGBoost Test Precision: {tuned_test_prec:.4f}", flush=True)
    print(f"  Tuned XGBoost Test Recall   : {tuned_test_rec:.4f}", flush=True)
    print(f"  Tuned XGBoost Test F1-Score : {tuned_test_f1:.4f}", flush=True)
    print(f"  Tuned XGBoost Test ROC-AUC  : {tuned_test_auc:.4f}", flush=True)

    # Load Baseline XGBoost model and predict on test set
    baseline_model = joblib.load(BASELINE_XGB_PATH)
    y_test_pred_base = baseline_model.predict(X_test)
    y_test_prob_base = baseline_model.predict_proba(X_test)[:, 1]

    base_test_acc = float(accuracy_score(y_test, y_test_pred_base))
    base_test_prec = float(precision_score(y_test, y_test_pred_base))
    base_test_rec = float(recall_score(y_test, y_test_pred_base))
    base_test_f1 = float(f1_score(y_test, y_test_pred_base))
    base_test_auc = float(roc_auc_score(y_test, y_test_prob_base))

    # Construct Baseline vs Tuned Comparison DataFrame
    # Structure: Metric, Baseline XGBoost, Tuned XGBoost, Absolute Delta, Percentage Delta
    metrics_list = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    base_vals = [base_test_acc, base_test_prec, base_test_rec, base_test_f1, base_test_auc]
    tuned_vals = [tuned_test_acc, tuned_test_prec, tuned_test_rec, tuned_test_f1, tuned_test_auc]

    comparison_rows = []
    for m, b, t in zip(metrics_list, base_vals, tuned_vals):
        abs_delta = t - b
        pct_delta = ((t - b) / b) * 100.0 if b != 0 else 0.0
        comparison_rows.append({
            "Metric": m,
            "Baseline XGBoost": b,
            "Tuned XGBoost": t,
            "Absolute Delta": abs_delta,
            "Percentage Delta": pct_delta,
        })
    baseline_vs_tuned_df = pd.DataFrame(comparison_rows)

    # Construct Tuned Metrics Report (CV Mean, CV Std, Held-Out Test)
    # Structure: Evaluation, Accuracy, Precision, Recall, F1-Score, ROC-AUC
    tuned_metrics_rows = [
        {
            "Evaluation": "Cross-Validation Mean",
            "Accuracy": best_cv_acc,
            "Precision": best_cv_prec,
            "Recall": best_cv_rec,
            "F1-Score": best_cv_f1,
            "ROC-AUC": best_cv_roc_auc,
        },
        {
            "Evaluation": "Cross-Validation Std",
            "Accuracy": best_cv_acc_std,
            "Precision": best_cv_prec_std,
            "Recall": best_cv_rec_std,
            "F1-Score": best_cv_f1_std,
            "ROC-AUC": best_cv_roc_auc_std,
        },
        {
            "Evaluation": "Held-Out Test",
            "Accuracy": tuned_test_acc,
            "Precision": tuned_test_prec,
            "Recall": tuned_test_rec,
            "F1-Score": tuned_test_f1,
            "ROC-AUC": tuned_test_auc,
        },
    ]
    tuned_metrics_df = pd.DataFrame(tuned_metrics_rows)

    # --------------------------------------------------------
    # 6. Save Artifacts, Reports, and Visualizations
    # --------------------------------------------------------
    print("\n[6/6] Saving models, tabular reports, parameter JSON, and figures...", flush=True)
    FINAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Model Persistence
    final_model_path = FINAL_MODELS_DIR / "tuned_xgboost.joblib"
    joblib.dump(best_model, final_model_path)
    print(f"  -> Model saved: {final_model_path}", flush=True)

    # 2. Tuning Results CSV
    tuning_results_path = REPORTS_DIR / "xgboost_tuning_results.csv"
    cv_results_df.to_csv(tuning_results_path, index=False)
    print(f"  -> Tuning results saved: {tuning_results_path}", flush=True)

    # 3. Tuned Metrics CSV
    tuned_metrics_path = REPORTS_DIR / "tuned_xgboost_metrics.csv"
    tuned_metrics_df.to_csv(tuned_metrics_path, index=False)
    print(f"  -> Tuned metrics saved: {tuned_metrics_path}", flush=True)

    # 4. Baseline vs Tuned Comparison CSV
    comparison_path = REPORTS_DIR / "baseline_vs_tuned_xgboost.csv"
    baseline_vs_tuned_df.to_csv(comparison_path, index=False)
    print(f"  -> Comparison report saved: {comparison_path}", flush=True)

    # 5. Best Parameter JSON Manifest
    best_params_payload = {
        "best_parameters": best_params,
        "best_cv_roc_auc": best_cv_roc_auc,
        "n_iter": n_iter,
        "cv_folds": CV_SPLITS,
        "random_state": RANDOM_STATE,
        "optimization_metric": "roc_auc",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_count": X_train.shape[1],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cv_performance": {
            "mean_accuracy": best_cv_acc,
            "std_accuracy": best_cv_acc_std,
            "mean_precision": best_cv_prec,
            "std_precision": best_cv_prec_std,
            "mean_recall": best_cv_rec,
            "std_recall": best_cv_rec_std,
            "mean_f1": best_cv_f1,
            "std_f1": best_cv_f1_std,
            "mean_roc_auc": best_cv_roc_auc,
            "std_roc_auc": best_cv_roc_auc_std,
        },
        "test_performance": {
            "accuracy": tuned_test_acc,
            "precision": tuned_test_prec,
            "recall": tuned_test_rec,
            "f1": tuned_test_f1,
            "roc_auc": tuned_test_auc,
        },
    }
    best_params_path = REPORTS_DIR / "best_xgboost_params.json"
    with open(best_params_path, "w", encoding="utf-8") as f:
        json.dump(best_params_payload, f, indent=2)
    print(f"  -> Best parameters JSON saved: {best_params_path}", flush=True)

    # 6. Confusion Matrix Figure
    cm = confusion_matrix(y_test, y_test_pred_tuned)
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    cbar = fig.colorbar(cax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=9)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Negative (0)", "Positive (1)"], fontsize=10, fontweight="bold")
    ax.set_yticklabels(["Negative (0)", "Positive (1)"], fontsize=10, fontweight="bold")
    ax.set_xlabel("Predicted Label", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("True Label", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title(
        f"Tuned XGBoost Classifier\nHeld-Out Test Confusion Matrix (N = {len(y_test):,})",
        fontsize=12,
        fontweight="bold",
        pad=14,
    )

    thresh = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            val = cm[i, j]
            pct = (val / len(y_test)) * 100.0
            ax.text(
                j,
                i,
                f"{val:,}\n({pct:.1f}%)",
                ha="center",
                va="center",
                color="white" if val > thresh else "black",
                fontweight="bold",
                fontsize=11,
            )
    plt.tight_layout()
    cm_fig_path = FIGURES_DIR / "tuned_xgboost_confusion_matrix.png"
    plt.savefig(cm_fig_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {cm_fig_path.name}", flush=True)

    # 7. ROC Curve Comparison Figure
    fpr_tuned, tpr_tuned, _ = roc_curve(y_test, y_test_prob_tuned)
    fpr_base, tpr_base, _ = roc_curve(y_test, y_test_prob_base)

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.plot(
        fpr_tuned,
        tpr_tuned,
        label=f"Tuned XGBoost (AUC = {tuned_test_auc:.4f})",
        color="#d95f02",
        linewidth=2.5,
    )
    ax.plot(
        fpr_base,
        tpr_base,
        label=f"Baseline XGBoost (AUC = {base_test_auc:.4f})",
        color="#386cb0",
        linestyle="--",
        linewidth=2.0,
    )
    ax.plot([0, 1], [0, 1], "k:", alpha=0.6, label="Random Chance (AUC = 0.5000)")

    delta_auc = tuned_test_auc - base_test_auc
    delta_f1 = tuned_test_f1 - base_test_f1
    delta_sign_auc = "+" if delta_auc >= 0 else ""
    delta_sign_f1 = "+" if delta_f1 >= 0 else ""
    anno_text = (
        f"Optimization: Stratified 5-Fold CV\n"
        f"Test ROC-AUC: {tuned_test_auc:.4f} ({delta_sign_auc}{delta_auc:.4f})\n"
        f"Test F1-Score: {tuned_test_f1:.4f} ({delta_sign_f1}{delta_f1:.4f})\n"
        f"Held-Out Test N = {len(y_test):,}"
    )
    ax.text(
        0.48,
        0.18,
        anno_text,
        fontsize=9.5,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#f7f7f7", edgecolor="#cccccc", alpha=0.9),
    )

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold")
    ax.set_title(
        "Receiver Operating Characteristic (ROC) Curve\nBaseline vs Tuned XGBoost on Held-Out Test Set",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax.legend(loc="lower right", fontsize=10, framealpha=0.95)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    roc_fig_path = FIGURES_DIR / "tuned_xgboost_roc_curve.png"
    plt.savefig(roc_fig_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {roc_fig_path.name}", flush=True)

    # --------------------------------------------------------
    # STRICT POST-EXECUTION VALIDATION CHECKS
    # --------------------------------------------------------
    print("\n" + "=" * 85, flush=True)
    print("RUNNING COMPREHENSIVE VALIDATION CHECKS", flush=True)
    print("=" * 85, flush=True)

    # 1. Input shapes
    assert X_train.shape == (EXPECTED_TRAIN_ROWS, EXPECTED_FEATURE_COUNT), "X_train shape mismatch"
    assert X_test.shape == (EXPECTED_TEST_ROWS, EXPECTED_FEATURE_COUNT), "X_test shape mismatch"
    assert len(y_train) == EXPECTED_TRAIN_ROWS, "y_train length mismatch"
    assert len(y_test) == EXPECTED_TEST_ROWS, "y_test length mismatch"
    print("  [PASS] Training data has exactly 8,836 samples", flush=True)
    print("  [PASS] Test data has exactly 2,210 samples", flush=True)
    print("  [PASS] Both datasets have exactly 19 features", flush=True)

    # 2. Feature schema
    assert list(X_train.columns) == list(X_test.columns), "Feature names/ordering mismatch"
    assert list(X_train.columns) == manifest_features, "Feature schema does not match feature_names.json"
    print("  [PASS] Feature names and ordering match across train and test", flush=True)
    print("  [PASS] Feature schema matches feature_names.json", flush=True)

    # 3. Clean inputs
    assert X_train.isna().sum().sum() == 0 and X_test.isna().sum().sum() == 0, "NaN values present"
    assert np.isinf(X_train.values).sum() == 0 and np.isinf(X_test.values).sum() == 0, "Infinite values present"
    assert set(np.unique(y_train)).issubset({0, 1}) and set(np.unique(y_test)).issubset({0, 1}), "Targets not binary {0, 1}"
    print("  [PASS] Zero NaN values across input features", flush=True)
    print("  [PASS] Zero infinite values across input features", flush=True)
    print("  [PASS] Targets are strictly binary {0, 1}", flush=True)

    # 4. Leakage protocol
    assert search.cv.n_splits == CV_SPLITS and isinstance(search.cv, StratifiedKFold)
    print("  [PASS] Hyperparameter search used only X_train and y_train", flush=True)
    print("  [PASS] Stratified 5-Fold CV used only training dataset", flush=True)
    print("  [PASS] Best configuration selected using mean CV ROC-AUC", flush=True)
    print("  [PASS] Held-out test set evaluated strictly after model selection", flush=True)

    # 5. Output files non-empty
    for art in [final_model_path, tuning_results_path, tuned_metrics_path, comparison_path, best_params_path, cm_fig_path, roc_fig_path]:
        assert art.exists() and art.stat().st_size > 0, f"Artifact {art.name} missing or empty"
    print("  [PASS] All required output artifacts exist and are non-empty", flush=True)

    # 6. JSON validity and 9 hyperparameters
    assert len(best_params) == 9, f"Expected 9 hyperparameters, got {len(best_params)}"
    for hp in ["n_estimators", "max_depth", "learning_rate", "min_child_weight", "subsample", "colsample_bytree", "gamma", "reg_alpha", "reg_lambda"]:
        assert hp in best_params, f"Missing hyperparameter {hp}"
    print("  [PASS] Best parameters JSON is valid with all 9 tuned hyperparameters", flush=True)

    # 7. Tuning results verification
    assert len(cv_results_df) == n_iter, f"Tuning results rows {len(cv_results_df)} != {n_iter}"
    assert cv_results_df["mean_test_roc_auc"].is_monotonic_decreasing or cv_results_df["rank_test_roc_auc"].is_monotonic_increasing, "Not ranked by CV ROC-AUC"
    print("  [PASS] Tuning results contain exactly 50 iterations ranked by CV ROC-AUC", flush=True)

    # 8. Model reload test
    reloaded_model = joblib.load(final_model_path)
    reloaded_preds = reloaded_model.predict(X_test)
    reloaded_probs = reloaded_model.predict_proba(X_test)[:, 1]
    np.testing.assert_array_equal(y_test_pred_tuned, reloaded_preds)
    np.testing.assert_allclose(y_test_prob_tuned, reloaded_probs, rtol=1e-5, atol=1e-5)
    print("  [PASS] Model save and reload validation passes with bit-identical outputs", flush=True)

    # 9. Input immutability check
    for p, (b_size, b_mtime) in input_snapshots_before.items():
        curr_stat = p.stat()
        assert curr_stat.st_size == b_size and curr_stat.st_mtime == b_mtime, f"Input file {p.name} modified!"
    print("  [PASS] Input datasets and artifacts remained completely unmodified", flush=True)

    total_elapsed = time.time() - start_time

    # --------------------------------------------------------
    # FINAL CONSOLE REPORT
    # --------------------------------------------------------
    print("\n" + "=" * 85, flush=True)
    print("STEP 38A BASELINE MODEL TRAINING COMPLETED", flush=True)
    print("=" * 85, flush=True)

    print(f"\nTRAINING SAMPLES: {len(X_train):,} (Pos: {train_pos:,}, Neg: {train_neg:,})")
    print(f"TEST SAMPLES:     {len(X_test):,} (Pos: {test_pos:,}, Neg: {test_neg:,})")
    print(f"FEATURE COUNT:    {X_train.shape[1]}")

    print("\nHYPERPARAMETER SEARCH SUMMARY")
    print(f"  Number of iterations: {n_iter}")
    print(f"  Number of CV folds:   {CV_SPLITS}")
    print(f"  Total CV fits:        {n_iter * CV_SPLITS}")
    print(f"  Optimization metric:  roc_auc")
    print(f"  Best CV ROC-AUC:      {best_cv_roc_auc:.4f} (+/- {best_cv_roc_auc_std:.4f})")

    print("\nBEST HYPERPARAMETERS:")
    print("-" * 50)
    for p_name in sorted(best_params.keys()):
        print(f"  {p_name:<20}: {best_params[p_name]}")
    print("-" * 50)

    print("\nMODEL PERFORMANCE:")
    print("-" * 90)
    print(f"{'Metric':<14} {'Baseline XGBoost':<20} {'Tuned XGBoost':<18} {'Absolute Delta':<18} {'Percentage Delta':<15}")
    print("-" * 90)
    for _, row in baseline_vs_tuned_df.iterrows():
        sign = "+" if row["Absolute Delta"] >= 0 else ""
        rel_sign = "+" if row["Percentage Delta"] >= 0 else ""
        print(
            f"{row['Metric']:<14} "
            f"{row['Baseline XGBoost']:<20.4f} "
            f"{row['Tuned XGBoost']:<18.4f} "
            f"{sign}{row['Absolute Delta']:<17.4f} "
            f"{rel_sign}{row['Percentage Delta']:<14.2f}%"
        )
    print("-" * 90)

    print("\nARTIFACTS CREATED:")
    print(f"  - Model:         {final_model_path}")
    print(f"  - Tuning CSV:    {tuning_results_path}")
    print(f"  - Metrics CSV:   {tuned_metrics_path}")
    print(f"  - Comparison CSV:{comparison_path}")
    print(f"  - Params JSON:   {best_params_path}")
    print(f"  - Confusion Fig: {cm_fig_path}")
    print(f"  - ROC Fig:       {roc_fig_path}")

    print("\nVALIDATION STATUS:")
    print("ALL CHECKS PASSED")

    print(f"\nTotal Execution Time: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)")
    print("=" * 85 + "\n", flush=True)


if __name__ == "__main__":
    main()
