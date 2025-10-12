"""
regime_drift_monitor.py
-----------------------
Monitors temporal drift in regime features and triggers retraining when needed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class DriftMonitor:
    def __init__(self, model_meta_path: Path, threshold: float = 0.25):
        self.meta_path = model_meta_path
        self.threshold = threshold
        self.ref_stats = self._load_reference_stats()

    def _load_reference_stats(self) -> Optional[dict]:
        """Load baseline mean and std from metadata if available."""
        if not self.meta_path.exists():
            print("⚠️ No metadata found for drift monitoring.")
            return None
        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return meta.get("feature_stats")

    def compute_feature_stats(self, features: pd.DataFrame) -> dict:
        """Compute mean and std for numeric features."""
        return {
            "mean": features.mean().to_dict(),
            "std": features.std().to_dict(),
        }

    def measure_drift(self, current_features: pd.DataFrame) -> float:
        """Compute average normalized deviation between current and baseline stats."""
        if not self.ref_stats:
            print("⚠️ No baseline stats; assuming maximum drift.")
            return 1.0

        current = self.compute_feature_stats(current_features)
        mean_diff = np.mean(
            [
                abs(current["mean"][k] - self.ref_stats["mean"].get(k, 0))
                for k in current["mean"].keys()
            ]
        )
        std_diff = np.mean(
            [
                abs(current["std"][k] - self.ref_stats["std"].get(k, 1))
                for k in current["std"].keys()
            ]
        )
        drift_score = (mean_diff + std_diff) / 2
        return float(drift_score)

    def has_drifted(self, current_features: pd.DataFrame) -> bool:
        score = self.measure_drift(current_features)
        print(f"🔍 Drift score: {score:.3f}")
        return score > self.threshold
