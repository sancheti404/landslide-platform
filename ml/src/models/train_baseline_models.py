"""
Step 37: Baseline Machine Learning Model Training and Evaluation Pipeline
for Uttarakhand Landslide Susceptibility Modeling.

This script trains, validates, and evaluates baseline machine learning models:
    1. Logistic Regression (with StandardScaler inside cross-validation pipeline)
    2. Random Forest Classifier
    3. XGBoost Classifier

Leakage-safe design:
    - Stratified 5-Fold Cross Validation performed strictly on X_train, y_train.
    - Test set (X_test, y_test) is evaluated exactly once after final training.
    - Probability predictions used for ROC-AUC.
    - Feature importances extracted for tree-based models.
    - All models, tabular reports, and visualization figures saved.
"""

import json
from pathlib import Path
import sys
import time

import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
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
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb


# ============================================================
# CONFIGURATION AND CONSTANTS
# ============================================================

DATA_SPLITS_DIR = Path("ml/data/processed/splits")
FEATURE_NAMES_PATH = Path("ml/models/preprocessing/feature_names.json")

MODELS_DIR = Path("ml/models/baseline")
REPORTS_DIR = Path("ml/reports/model_evaluation")
FIGURES_DIR = REPORTS_DIR / "figures"

X_TRAIN_PATH = DATA_SPLITS_DIR / "X_train.csv"
X_TEST_PATH = DATA_SPLITS_DIR / "X_test.csv"
Y_TRAIN_PATH = DATA_SPLITS_DIR / "y_train.csv"
Y_TEST_PATH = DATA_SPLITS_DIR / "y_test.csv"

RANDOM_STATE = 42
CV_SPLITS = 5

EXPECTED_TRAIN_ROWS = 8836
EXPECTED_TEST_ROWS = 2210
EXPECTED_FEATURE_COUNT = 19


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    start_time = time.time()

    print("=" * 80, flush=True)
    print("STEP 37 — BASELINE MACHINE LEARNING MODEL TRAINING", flush=True)
    print("=" * 80, flush=True)

    # --------------------------------------------------------
    # 1. Input Validation
    # --------------------------------------------------------
    print("\n[1/6] Loading and validating input datasets...", flush=True)
    for p in [X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH, FEATURE_NAMES_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Required input missing: {p}")

    # Track immutability
    input_file_stats = {p: (p.stat().st_size, p.stat().st_mtime) for p in [X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH]}

    X_train = pd.read_csv(X_TRAIN_PATH)
    X_test = pd.read_csv(X_TEST_PATH)
    y_train_df = pd.read_csv(Y_TRAIN_PATH)
    y_test_df = pd.read_csv(Y_TEST_PATH)

    y_train = y_train_df["landslide"].values
    y_test = y_test_df["landslide"].values

    with open(FEATURE_NAMES_PATH, "r", encoding="utf-8") as f:
        feature_manifest = json.load(f)
    manifest_features = feature_manifest["final_transformed_feature_names"]

    # Strict input assertions
    if len(X_train) != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"X_train rows {len(X_train)} != {EXPECTED_TRAIN_ROWS}")
    if len(X_test) != EXPECTED_TEST_ROWS:
        raise ValueError(f"X_test rows {len(X_test)} != {EXPECTED_TEST_ROWS}")
    if len(y_train) != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"y_train rows {len(y_train)} != {EXPECTED_TRAIN_ROWS}")
    if len(y_test) != EXPECTED_TEST_ROWS:
        raise ValueError(f"y_test rows {len(y_test)} != {EXPECTED_TEST_ROWS}")

    if X_train.shape[1] != EXPECTED_FEATURE_COUNT or X_test.shape[1] != EXPECTED_FEATURE_COUNT:
        raise ValueError(f"Feature count mismatch: expected {EXPECTED_FEATURE_COUNT}")

    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("X_train and X_test column names/order mismatch")
    if list(X_train.columns) != manifest_features:
        raise ValueError("X_train columns do not match feature_names.json manifest")

    if X_train.isna().sum().sum() > 0 or X_test.isna().sum().sum() > 0:
        raise ValueError("Input features contain missing values (NaN)")

    if np.isinf(X_train.values).sum() > 0 or np.isinf(X_test.values).sum() > 0:
        raise ValueError("Input features contain infinite values (+/-Inf)")

    if not set(np.unique(y_train)).issubset({0, 1}) or not set(np.unique(y_test)).issubset({0, 1}):
        raise ValueError("Target labels contain values outside {0, 1}")

    print(f"  Training samples: {len(X_train):,} (Pos: {np.sum(y_train == 1):,}, Neg: {np.sum(y_train == 0):,})", flush=True)
    print(f"  Testing samples : {len(X_test):,} (Pos: {np.sum(y_test == 1):,}, Neg: {np.sum(y_test == 0):,})", flush=True)
    print(f"  Feature count   : {X_train.shape[1]} features", flush=True)

    # --------------------------------------------------------
    # 2. Define Baseline Models
    # --------------------------------------------------------
    print("\n[2/6] Configuring baseline machine learning models...", flush=True)

    # Model 1: Logistic Regression with StandardScaler in pipeline to prevent fold leakage
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
    ])

    # Model 2: Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    # Model 3: XGBoost
    xgb_model = xgb.XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric="logloss",
    )

    models = {
        "Logistic Regression": lr_pipeline,
        "Random Forest": rf_model,
        "XGBoost": xgb_model,
    }

    # --------------------------------------------------------
    # 3. Stratified 5-Fold Cross Validation (Training Set Only)
    # --------------------------------------------------------
    print(f"\n[3/6] Running Stratified {CV_SPLITS}-Fold Cross-Validation on training data only...", flush=True)
    cv = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    scoring_metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]

    cv_detailed_rows = []
    cv_summary = {}

    for name, model in models.items():
        print(f"  Evaluating {name} with 5-fold CV...", end=" ", flush=True)
        t0 = time.time()
        cv_res = cross_validate(
            model,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring_metrics,
            return_train_score=False,
            n_jobs=-1 if name == "Logistic Regression" else None,
        )
        t_elapsed = time.time() - t0

        acc_mean, acc_std = float(cv_res["test_accuracy"].mean()), float(cv_res["test_accuracy"].std())
        prec_mean, prec_std = float(cv_res["test_precision"].mean()), float(cv_res["test_precision"].std())
        rec_mean, rec_std = float(cv_res["test_recall"].mean()), float(cv_res["test_recall"].std())
        f1_mean, f1_std = float(cv_res["test_f1"].mean()), float(cv_res["test_f1"].std())
        auc_mean, auc_std = float(cv_res["test_roc_auc"].mean()), float(cv_res["test_roc_auc"].std())

        cv_summary[name] = {
            "cv_accuracy": acc_mean,
            "cv_accuracy_std": acc_std,
            "cv_precision": prec_mean,
            "cv_precision_std": prec_std,
            "cv_recall": rec_mean,
            "cv_recall_std": rec_std,
            "cv_f1": f1_mean,
            "cv_f1_std": f1_std,
            "cv_roc_auc": auc_mean,
            "cv_roc_auc_std": auc_std,
        }

        for fold_idx in range(CV_SPLITS):
            cv_detailed_rows.append({
                "model": name,
                "fold": fold_idx + 1,
                "accuracy": float(cv_res["test_accuracy"][fold_idx]),
                "precision": float(cv_res["test_precision"][fold_idx]),
                "recall": float(cv_res["test_recall"][fold_idx]),
                "f1": float(cv_res["test_f1"][fold_idx]),
                "roc_auc": float(cv_res["test_roc_auc"][fold_idx]),
            })

        print(f"Done in {t_elapsed:.1f}s | CV ROC-AUC: {auc_mean:.4f} (+/- {auc_std:.4f}), F1: {f1_mean:.4f}", flush=True)

    # --------------------------------------------------------
    # 4. Final Training and Test Evaluation
    # --------------------------------------------------------
    print("\n[4/6] Fitting final models on full training set and evaluating on test set...", flush=True)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    test_summary = {}
    fitted_models = {}
    test_roc_curves = {}
    confusion_matrices = {}
    class_reports = {}

    for name, model in models.items():
        print(f"  Fitting {name} on X_train (8,836 samples)...", end=" ", flush=True)
        t0 = time.time()
        model.fit(X_train, y_train)
        t_fit = time.time() - t0
        fitted_models[name] = model

        # Predict on test set
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred))
        rec = float(recall_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred))
        auc = float(roc_auc_score(y_test, y_prob))

        test_summary[name] = {
            "test_accuracy": acc,
            "test_precision": prec,
            "test_recall": rec,
            "test_f1": f1,
            "test_roc_auc": auc,
        }

        cm = confusion_matrix(y_test, y_pred)
        confusion_matrices[name] = cm
        class_reports[name] = classification_report(y_test, y_pred, digits=4)

        fpr, tpr, thresholds = roc_curve(y_test, y_prob)
        test_roc_curves[name] = (fpr, tpr, auc)

        print(f"Done in {t_fit:.1f}s | Test ROC-AUC: {auc:.4f}, Test F1: {f1:.4f}", flush=True)

    # --------------------------------------------------------
    # 5. Save Models, Tabular Reports, and Feature Importance
    # --------------------------------------------------------
    print("\n[5/6] Saving models, evaluation tables, and feature importances...", flush=True)

    # Save models
    saved_model_paths = {
        "Logistic Regression": MODELS_DIR / "logistic_regression.joblib",
        "Random Forest": MODELS_DIR / "random_forest.joblib",
        "XGBoost": MODELS_DIR / "xgboost.joblib",
    }
    for name, path in saved_model_paths.items():
        joblib.dump(fitted_models[name], path)
        print(f"  -> Saved model: {path}")

    # Build and save comparison table
    comparison_rows = []
    for name in models.keys():
        cv_s = cv_summary[name]
        te_s = test_summary[name]
        comparison_rows.append({
            "Model": name,
            "CV Accuracy": cv_s["cv_accuracy"],
            "CV Precision": cv_s["cv_precision"],
            "CV Recall": cv_s["cv_recall"],
            "CV F1": cv_s["cv_f1"],
            "CV ROC-AUC": cv_s["cv_roc_auc"],
            "Test Accuracy": te_s["test_accuracy"],
            "Test Precision": te_s["test_precision"],
            "Test Recall": te_s["test_recall"],
            "Test F1": te_s["test_f1"],
            "Test ROC-AUC": te_s["test_roc_auc"],
        })
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_path = REPORTS_DIR / "baseline_model_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"  -> Saved comparison table: {comparison_path}")

    # Save detailed CV results
    cv_detailed_df = pd.DataFrame(cv_detailed_rows)
    cv_detailed_path = REPORTS_DIR / "cross_validation_results.csv"
    cv_detailed_df.to_csv(cv_detailed_path, index=False)
    print(f"  -> Saved detailed CV table: {cv_detailed_path}")

    # Extract and save Feature Importance for tree models
    rf_fitted = fitted_models["Random Forest"]
    rf_importances = rf_fitted.feature_importances_
    rf_fi_df = pd.DataFrame({
        "feature": manifest_features,
        "importance": rf_importances,
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)
    rf_fi_path = REPORTS_DIR / "random_forest_feature_importance.csv"
    rf_fi_df.to_csv(rf_fi_path, index=False)
    print(f"  -> Saved RF feature importance: {rf_fi_path}")

    xgb_fitted = fitted_models["XGBoost"]
    xgb_importances = xgb_fitted.feature_importances_
    xgb_fi_df = pd.DataFrame({
        "feature": manifest_features,
        "importance": xgb_importances,
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)
    xgb_fi_path = REPORTS_DIR / "xgboost_feature_importance.csv"
    xgb_fi_df.to_csv(xgb_fi_path, index=False)
    print(f"  -> Saved XGB feature importance: {xgb_fi_path}")

    # --------------------------------------------------------
    # 6. Generate Evaluation Visualizations
    # --------------------------------------------------------
    print("\n[6/6] Generating evaluation figures...", flush=True)

    # A. Confusion Matrices
    cm_paths = {}
    for name, cm in confusion_matrices.items():
        slug = name.lower().replace(" ", "_")
        fig, ax = plt.subplots(figsize=(5.5, 4.5))
        cax = ax.imshow(cm, interpolation="nearest", cmap="Blues")
        fig.colorbar(cax, fraction=0.046, pad=0.04)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Negative (0)", "Positive (1)"], fontsize=10)
        ax.set_yticklabels(["Negative (0)", "Positive (1)"], fontsize=10)
        ax.set_xlabel("Predicted Label", fontsize=11, fontweight="bold")
        ax.set_ylabel("True Label", fontsize=11, fontweight="bold")
        ax.set_title(f"{name}\nTest Confusion Matrix", fontsize=12, fontweight="bold", pad=12)

        thresh = cm.max() / 2.0
        for i in range(2):
            for j in range(2):
                val = cm[i, j]
                ax.text(
                    j, i, f"{val:,}\n({val/len(y_test)*100:.1f}%)",
                    ha="center", va="center",
                    color="white" if val > thresh else "black",
                    fontweight="bold", fontsize=11
                )
        plt.tight_layout()
        cm_path = FIGURES_DIR / f"{slug}_confusion_matrix.png"
        plt.savefig(cm_path, dpi=300)
        plt.close()
        cm_paths[name] = cm_path
        print(f"  -> Generated: {cm_path.name}")

    # B. ROC Curve Comparison
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = {"Logistic Regression": "#386cb0", "Random Forest": "#2ca02c", "XGBoost": "#d95f02"}
    for name, (fpr, tpr, auc_val) in test_roc_curves.items():
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc_val:.4f})", color=colors[name], linewidth=2.2)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.7, label="Random Chance (AUC = 0.5000)")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold")
    ax.set_title("Receiver Operating Characteristic (ROC) Comparison\nTest Set Evaluation (N = 2,210)", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    roc_path = FIGURES_DIR / "roc_curve_comparison.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {roc_path.name}")

    # C. Model Comparison Chart (Accuracy, F1, ROC-AUC)
    fig, ax = plt.subplots(figsize=(8, 5))
    models_list = list(models.keys())
    x = np.arange(len(models_list))
    width = 0.25

    acc_scores = [test_summary[m]["test_accuracy"] for m in models_list]
    f1_scores = [test_summary[m]["test_f1"] for m in models_list]
    auc_scores = [test_summary[m]["test_roc_auc"] for m in models_list]

    bars1 = ax.bar(x - width, acc_scores, width, label="Accuracy", color="#386cb0", edgecolor="black")
    bars2 = ax.bar(x, f1_scores, width, label="F1-Score", color="#7fc97f", edgecolor="black")
    bars3 = ax.bar(x + width, auc_scores, width, label="ROC-AUC", color="#fdc086", edgecolor="black")

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.012, f"{h:.3f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_ylim(0.70, 1.02)
    ax.set_xticks(x)
    ax.set_xticklabels(models_list, fontsize=11, fontweight="bold")
    ax.set_ylabel("Metric Score", fontsize=11, fontweight="bold")
    ax.set_title("Baseline Model Performance Comparison on Test Set", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="lower left", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    comp_chart_path = FIGURES_DIR / "baseline_model_comparison.png"
    plt.savefig(comp_chart_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {comp_chart_path.name}")

    # D. Feature Importance Plots
    for name, fi_df, fi_slug in [("Random Forest", rf_fi_df, "random_forest"), ("XGBoost", xgb_fi_df, "xgboost")]:
        fig, ax = plt.subplots(figsize=(10, 7))
        y_pos = np.arange(len(fi_df))
        ax.barh(y_pos, fi_df["importance"].values[::-1], color="#2b5c8f" if "Forest" in name else "#d95f02", alpha=0.85, edgecolor="black")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(fi_df["feature"].values[::-1], fontsize=9)
        ax.set_xlabel("Relative Feature Importance", fontsize=11, fontweight="bold")
        ax.set_title(f"{name} Baseline Feature Importance\n(19 Transformed ML Predictors)", fontsize=12, fontweight="bold", pad=12)
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        for i, v in enumerate(fi_df["importance"].values[::-1]):
            ax.text(v + 0.003, i, f"{v:.3f}", va="center", fontsize=8.5)
        plt.tight_layout()
        fi_plot_path = FIGURES_DIR / f"{fi_slug}_feature_importance.png"
        plt.savefig(fi_plot_path, dpi=300)
        plt.close()
        print(f"  -> Generated: {fi_plot_path.name}")

    # --------------------------------------------------------
    # STRICT VALIDATION CHECKS
    # --------------------------------------------------------
    print("\nRunning comprehensive validation checks...", flush=True)

    # 1. Model reload verification
    for name, path in saved_model_paths.items():
        reloaded = joblib.load(path)
        pred_orig = fitted_models[name].predict(X_test)
        pred_reloaded = reloaded.predict(X_test)
        if not np.array_equal(pred_orig, pred_reloaded):
            raise ValueError(f"Model reload verification failed for {name}")
    print("  -> Model reload validation: PASSED", flush=True)

    # 2. Feature importance length check
    if len(rf_fi_df) != EXPECTED_FEATURE_COUNT or len(xgb_fi_df) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Feature importance vector length != 19")
    print("  -> Feature importance vector length validation: PASSED", flush=True)

    # 3. Input files immutability check
    for p, (b_size, b_mtime) in input_file_stats.items():
        s = p.stat()
        if s.st_size != b_size or s.st_mtime != b_mtime:
            raise ValueError(f"Input file {p.name} was modified during execution!")
    print("  -> Input datasets immutability validation: PASSED", flush=True)

    # Identify best models
    best_cv_model = max(cv_summary.keys(), key=lambda m: cv_summary[m]["cv_roc_auc"])
    best_test_model = max(test_summary.keys(), key=lambda m: test_summary[m]["test_roc_auc"])

    # --------------------------------------------------------
    # FINAL CONSOLE REPORT
    # --------------------------------------------------------
    elapsed = time.time() - start_time

    print("\n" + "=" * 80, flush=True)
    print("STEP 37 BASELINE MODEL TRAINING COMPLETED", flush=True)
    print("=" * 80, flush=True)

    print(f"\nTRAINING SAMPLES: {len(X_train):,}")
    print(f"TEST SAMPLES:     {len(X_test):,}")
    print(f"FEATURE COUNT:    {X_train.shape[1]}")

    print("\nCROSS-VALIDATION RESULTS (Stratified 5-Fold on Training Set Only):")
    print("-" * 95)
    print(f"{'Model':<22} {'CV Accuracy':<15} {'CV Precision':<15} {'CV Recall':<15} {'CV F1':<15} {'CV ROC-AUC':<15}")
    print("-" * 95)
    for name in models.keys():
        s = cv_summary[name]
        print(
            f"{name:<22} "
            f"{s['cv_accuracy']:.4f}±{s['cv_accuracy_std']:.3f}   "
            f"{s['cv_precision']:.4f}±{s['cv_precision_std']:.3f}   "
            f"{s['cv_recall']:.4f}±{s['cv_recall_std']:.3f}   "
            f"{s['cv_f1']:.4f}±{s['cv_f1_std']:.3f}   "
            f"{s['cv_roc_auc']:.4f}±{s['cv_roc_auc_std']:.3f}"
        )
    print("-" * 95)

    print("\nFINAL TEST RESULTS (Evaluated Once on Held-Out Test Set):")
    print("-" * 80)
    print(f"{'Model':<22} {'Accuracy':<11} {'Precision':<11} {'Recall':<11} {'F1-Score':<11} {'ROC-AUC':<11}")
    print("-" * 80)
    for name in models.keys():
        s = test_summary[name]
        print(
            f"{name:<22} "
            f"{s['test_accuracy']:.4f}      "
            f"{s['test_precision']:.4f}      "
            f"{s['test_recall']:.4f}      "
            f"{s['test_f1']:.4f}      "
            f"{s['test_roc_auc']:.4f}"
        )
    print("-" * 80)

    print(f"\nBEST BASELINE MODEL BY CV ROC-AUC:   {best_cv_model} (CV ROC-AUC = {cv_summary[best_cv_model]['cv_roc_auc']:.4f})")
    print(f"BEST BASELINE MODEL BY TEST ROC-AUC: {best_test_model} (Test ROC-AUC = {test_summary[best_test_model]['test_roc_auc']:.4f})")

    print("\nARTIFACTS CREATED:")
    print("  Models:")
    for p in saved_model_paths.values():
        print(f"    - {p}")
    print("  Reports:")
    print(f"    - {comparison_path}")
    print(f"    - {cv_detailed_path}")
    print(f"    - {rf_fi_path}")
    print(f"    - {xgb_fi_path}")
    print("  Figures:")
    for p in cm_paths.values():
        print(f"    - {p}")
    print(f"    - {roc_path}")
    print(f"    - {comp_chart_path}")
    print(f"    - {FIGURES_DIR / 'random_forest_feature_importance.png'}")
    print(f"    - {FIGURES_DIR / 'xgboost_feature_importance.png'}")

    print("\nVALIDATION STATUS:")
    print("ALL CHECKS PASSED")

    print(f"\nExecution Time: {elapsed:.2f} seconds")
    print("=" * 80 + "\n", flush=True)


if __name__ == "__main__":
    main()
