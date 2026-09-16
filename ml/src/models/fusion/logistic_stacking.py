"""
Logistic Stacking Meta-Model Module for Multimodal Landslide Susceptibility Modeling.
Uttarakhand Landslide Intelligence Platform.

Fits a lightweight regularized LogisticRegression meta-classifier on out-of-fold/validation
probabilities from the tabular XGBoost branch and deep visual Swin Transformer branch:
    z = beta_0 + beta_xgb * P_xgb + beta_swin * P_swin
    P_fused = 1 / (1 + exp(-z))

Strictly trained on validation/OOF data only; held-out test predictions are never used during fitting.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


class LogisticStackingFusion:
    """
    Logistic Stacking meta-model combining base model probabilities.
    """

    def __init__(self, C: float = 1.0, random_state: int = 42, threshold: float = 0.5):
        self.C = float(C)
        self.random_state = int(random_state)
        self.threshold = float(threshold)
        self.clf = LogisticRegression(
            C=self.C,
            solver="lbfgs",
            penalty="l2",
            random_state=self.random_state,
            max_iter=1000,
        )
        self.is_fitted_ = False
        self.validation_metrics_: Optional[Dict[str, float]] = None

    def fit(self, p_xgb: np.ndarray, p_swin: np.ndarray, y_true: np.ndarray) -> "LogisticStackingFusion":
        """
        Fits the regularized LogisticRegression meta-model strictly on OOF/validation data.

        Args:
            p_xgb: Validation probabilities from XGBoost branch (shape [N,]).
            p_swin: Validation probabilities from Swin Transformer branch (shape [N,]).
            y_true: True binary labels (shape [N,]).

        Returns:
            self with fitted coefficients.
        """
        p_xgb = np.asarray(p_xgb, dtype=float).ravel()
        p_swin = np.asarray(p_swin, dtype=float).ravel()
        y_true = np.asarray(y_true, dtype=int).ravel()

        if len(p_xgb) != len(p_swin) or len(p_xgb) != len(y_true):
            raise ValueError(f"Length mismatch: p_xgb={len(p_xgb)}, p_swin={len(p_swin)}, y_true={len(y_true)}")

        X = np.column_stack([p_xgb, p_swin])
        self.clf.fit(X, y_true)
        self.is_fitted_ = True

        # Compute validation performance
        probs = self.predict_proba(p_xgb, p_swin)
        preds = (probs >= self.threshold).astype(int)

        roc_auc = roc_auc_score(y_true, probs)
        prec_curve, rec_curve, _ = precision_recall_curve(y_true, probs)
        pr_auc = auc(rec_curve, prec_curve)
        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds, zero_division=0)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        brier = brier_score_loss(y_true, probs)

        self.validation_metrics_ = {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "brier_score": brier,
            "coef_xgb": float(self.clf.coef_[0][0]),
            "coef_swin": float(self.clf.coef_[0][1]),
            "intercept": float(self.clf.intercept_[0]),
        }

        return self

    def predict_proba(self, p_xgb: np.ndarray, p_swin: np.ndarray) -> np.ndarray:
        """
        Predicts calibrated posterior probability from stacked base predictions.
        """
        if not self.is_fitted_:
            raise RuntimeError("LogisticStackingFusion meta-model is not fitted yet.")

        p_xgb = np.asarray(p_xgb, dtype=float).ravel()
        p_swin = np.asarray(p_swin, dtype=float).ravel()

        if len(p_xgb) != len(p_swin):
            raise ValueError(f"Length mismatch: p_xgb={len(p_xgb)}, p_swin={len(p_swin)}")

        X = np.column_stack([p_xgb, p_swin])
        probs = self.clf.predict_proba(X)[:, 1]
        return np.clip(probs, 0.0, 1.0)

    def predict(self, p_xgb: np.ndarray, p_swin: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """
        Predicts binary classification output using decision threshold.
        """
        th = self.threshold if threshold is None else threshold
        probs = self.predict_proba(p_xgb, p_swin)
        return (probs >= th).astype(int)

    def get_params(self) -> Dict[str, float]:
        """Returns logistic model coefficients and intercept."""
        if not self.is_fitted_:
            raise RuntimeError("Model is not fitted.")
        return {
            "intercept": float(self.clf.intercept_[0]),
            "coef_xgb": float(self.clf.coef_[0][0]),
            "coef_swin": float(self.clf.coef_[0][1]),
        }

    def save(self, filepath: Union[str, Path]):
        """Saves meta-model to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "LogisticStackingFusion":
        """Loads serialized meta-model."""
        return joblib.load(filepath)
