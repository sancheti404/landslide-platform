"""
Weighted Late Fusion Module for Multimodal Landslide Susceptibility Modeling.
Uttarakhand Landslide Intelligence Platform.

Combines calibrated probabilities from the tabular XGBoost branch and deep visual
Swin Transformer branch:
    P_fused = w_xgb * P_xgb + w_swin * P_swin
    subject to: w_xgb >= 0, w_swin >= 0, w_xgb + w_swin = 1.0

Strictly optimizes weights using validation/OOF data only.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    auc,
)


@dataclass
class WeightedFusionResult:
    w_xgb: float
    w_swin: float
    roc_auc: float
    pr_auc: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    brier_score: float


class WeightedLateFusion:
    """
    Weighted Late Fusion model for combining independent probabilistic branch predictions.
    """

    def __init__(self, w_xgb: Optional[float] = None, w_swin: Optional[float] = None, threshold: float = 0.5):
        if w_xgb is not None and w_swin is not None:
            if not np.isclose(w_xgb + w_swin, 1.0, atol=1e-5):
                raise ValueError(f"Weights must sum to 1.0, got w_xgb={w_xgb}, w_swin={w_swin}")
            self.w_xgb = float(w_xgb)
            self.w_swin = float(w_swin)
        else:
            self.w_xgb = None
            self.w_swin = None
        self.threshold = float(threshold)
        self.grid_results_: Optional[pd.DataFrame] = None
        self.best_metrics_: Optional[Dict[str, float]] = None

    def fit(
        self,
        p_xgb: np.ndarray,
        p_swin: np.ndarray,
        y_true: np.ndarray,
        metric: str = "roc_auc",
        grid_step: float = 0.01,
    ) -> "WeightedLateFusion":
        """
        Searches a fine 1D grid of candidate weights w_xgb in [0.0, 1.0], w_swin = 1.0 - w_xgb,
        evaluating each configuration on the validation dataset.

        Args:
            p_xgb: Validation probabilities from XGBoost branch (shape [N,]).
            p_swin: Validation probabilities from Swin Transformer branch (shape [N,]).
            y_true: True binary labels (shape [N,]).
            metric: Selection criterion ('roc_auc', 'f1', 'pr_auc', 'brier_score').
            grid_step: Granularity of weight search (default 0.01 = 101 candidates).

        Returns:
            self with optimal weights frozen.
        """
        p_xgb = np.asarray(p_xgb, dtype=float).ravel()
        p_swin = np.asarray(p_swin, dtype=float).ravel()
        y_true = np.asarray(y_true, dtype=int).ravel()

        if len(p_xgb) != len(p_swin) or len(p_xgb) != len(y_true):
            raise ValueError(
                f"Array length mismatch: p_xgb={len(p_xgb)}, p_swin={len(p_swin)}, y_true={len(y_true)}"
            )

        weights_xgb = np.linspace(0.0, 1.0, int(round(1.0 / grid_step)) + 1)
        records = []

        for w in weights_xgb:
            w_x = float(w)
            w_s = float(1.0 - w)
            fused_prob = w_x * p_xgb + w_s * p_swin
            fused_prob = np.clip(fused_prob, 0.0, 1.0)
            fused_pred = (fused_prob >= self.threshold).astype(int)

            roc_auc = roc_auc_score(y_true, fused_prob)
            prec_curve, rec_curve, _ = precision_recall_curve(y_true, fused_prob)
            pr_auc = auc(rec_curve, prec_curve)
            acc = accuracy_score(y_true, fused_pred)
            prec = precision_score(y_true, fused_pred, zero_division=0)
            rec = recall_score(y_true, fused_pred, zero_division=0)
            f1 = f1_score(y_true, fused_pred, zero_division=0)
            brier = brier_score_loss(y_true, fused_prob)

            records.append({
                "w_xgb": round(w_x, 4),
                "w_swin": round(w_s, 4),
                "roc_auc": roc_auc,
                "pr_auc": pr_auc,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "brier_score": brier,
            })

        self.grid_results_ = pd.DataFrame(records)

        # Select best weight according to specified metric
        if metric == "brier_score":
            best_idx = self.grid_results_[metric].idxmin()
        else:
            best_idx = self.grid_results_[metric].idxmax()

        best_row = self.grid_results_.loc[best_idx]
        self.w_xgb = float(best_row["w_xgb"])
        self.w_swin = float(best_row["w_swin"])
        self.best_metrics_ = best_row.to_dict()

        return self

    def predict_proba(self, p_xgb: np.ndarray, p_swin: np.ndarray) -> np.ndarray:
        """
        Computes fused probabilities: w_xgb * p_xgb + w_swin * p_swin.
        """
        if self.w_xgb is None or self.w_swin is None:
            raise RuntimeError("WeightedLateFusion model is not fitted yet.")

        p_xgb = np.asarray(p_xgb, dtype=float).ravel()
        p_swin = np.asarray(p_swin, dtype=float).ravel()

        if len(p_xgb) != len(p_swin):
            raise ValueError(f"Length mismatch: p_xgb={len(p_xgb)}, p_swin={len(p_swin)}")

        fused = self.w_xgb * p_xgb + self.w_swin * p_swin
        return np.clip(fused, 0.0, 1.0)

    def predict(self, p_xgb: np.ndarray, p_swin: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """
        Predicts binary classification output using decision threshold.
        """
        th = self.threshold if threshold is None else threshold
        probs = self.predict_proba(p_xgb, p_swin)
        return (probs >= th).astype(int)

    def get_weights(self) -> Tuple[float, float]:
        """Returns tuple (w_xgb, w_swin)."""
        return self.w_xgb, self.w_swin

    def save(self, filepath: Union[str, Path]):
        """Serializes model parameters and metadata to JSON."""
        data = {
            "model_type": "WeightedLateFusion",
            "w_xgb": self.w_xgb,
            "w_swin": self.w_swin,
            "threshold": self.threshold,
            "best_metrics": self.best_metrics_,
        }
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "WeightedLateFusion":
        """Loads serialized model parameters from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        instance = cls(w_xgb=data["w_xgb"], w_swin=data["w_swin"], threshold=data.get("threshold", 0.5))
        instance.best_metrics_ = data.get("best_metrics")
        return instance
