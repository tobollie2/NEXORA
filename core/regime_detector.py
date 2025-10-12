# File: core/regime_detector.py

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class RegimeDetector:
    """
    Classifies market regimes based on statistical + ML signals.
    Modes:
      - Statistical (threshold-based)
      - ML (adaptive clustering)
    """

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.config = config or {}
        self.mode = self.config.get("regime_mode", "hybrid")  # "stat", "ml", or "hybrid"
        self.n_clusters = self.config.get("n_regimes", 3)

        self.scaler = StandardScaler()
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.last_regime = None
        self.feature_history = pd.DataFrame()

        self.regime_labels = {0: "TREND", 1: "MEAN_REVERT", 2: "VOLATILE"}

    # -----------------------------
    # Update regime classification
    # -----------------------------

    def classify(self, features: pd.DataFrame) -> str:
        """Determine the current regime based on most recent features."""
        if features.empty:
            return self.last_regime or "UNKNOWN"

        self.feature_history = pd.concat([self.feature_history, features]).tail(500)

        # --- Statistical mode ---
        vol = features["volatility_10"].values[0]
        mom = features["momentum_10"].values[0]
        zscore = features["zscore_ret"].values[0]

        if self.mode in ["stat", "hybrid"]:
            if vol < 0.001 and abs(mom) < 0.002:
                regime = "MEAN_REVERT"
            elif abs(mom) > 0.005:
                regime = "TREND"
            else:
                regime = "VOLATILE"

        # --- ML mode ---
        if self.mode in ["ml", "hybrid"] and len(self.feature_history) > 50:
            # use only numeric columns
            X = self.feature_history.select_dtypes(include=np.number).fillna(0)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            regime_id = self.model.predict(
                self.scaler.transform(features.select_dtypes(include=np.number))
            )[0]
            regime_ml = self.regime_labels.get(regime_id, "UNKNOWN")

            if self.mode == "ml":
                regime = regime_ml
            else:
                # hybrid voting
                if regime_ml != regime:
                    regime = regime_ml  # override when disagreement is strong

        self.last_regime = regime
        if self.logger:
            self.logger.info(f"📈 Regime classified as {regime}")

        return regime

    def get_regime(self):
        """Return the last classified regime."""
        return self.last_regime or "UNKNOWN"
