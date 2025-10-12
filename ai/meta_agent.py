"""
meta_agent.py — Phase 9.7 Adaptive Drift Integration
----------------------------------------------------
Central coordinating intelligence for Nexora’s multi-agent system.
Adds:
  • Drift monitoring via DriftMonitor
  • Automatic retraining of RegimeLSTM when drift exceeds threshold
  • Confidence-weighted adaptation for regime reliability
  • Thread-safe background updates to avoid blocking live execution
"""

from __future__ import annotations

import sys
import json
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

from ai.models.regime_forecaster import RegimeForecaster
from ai.models.regime_drift_monitor import DriftMonitor
from ai.models.regime_lstm_trainer import train_regime_lstm, load_regime_model


# Ensure project root discoverable for nested imports
sys.path.append(str(Path(__file__).resolve().parents[1]))


class MetaAgent:
    """Adaptive meta-controller coordinating strategy agents and managing regime awareness."""

    # ---------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------
    def __init__(self, model_path: str | Path = "F:/NEXORA/ai/models/regime_lstm.pt"):
        self.model_path = Path(model_path)
        self.model_dir = self.model_path.parent

        # Regime forecaster (loads pretrained model)
        self.regime_forecaster = RegimeForecaster(
            model_path=self.model_path,
            model_meta_path=self.model_dir / "regime_lstm.meta.json",
        )

        self.current_regime: str | None = None

        # Confidence tracking
        self.regime_confidence: float = 1.0
        self.retraining: bool = False
        self.last_drift_score: float = 0.0

        # Drift monitor setup
        self.drift_monitor = DriftMonitor(
            model_meta_path=self.model_dir / "regime_lstm.meta.json", threshold=0.25
        )

        # Telemetry for drift history and confidence evolution
        self.telemetry: list[Dict[str, Any]] = []

        print("✅ MetaAgent initialized — regime model loaded and drift monitor ready.")

    # ---------------------------------------------------------------
    # Core Evaluation
    # ---------------------------------------------------------------
    def evaluate_agents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate underlying agents given incoming data.

        Expected data keys:
            - 'prices'   : pd.DataFrame of asset prices
            - 'features' : pd.DataFrame of extracted temporal features
        """
        prices = data.get("prices")
        features = data.get("features")

        if prices is None or features is None:
            print("⚠️ Missing input data for MetaAgent evaluation.")
            return {"error": "missing_data"}

        # Predict current regime
        self.current_regime = self.regime_forecaster.predict_regime(prices)
        print(f"📈 Current regime identified as: {self.current_regime}")

        # Monitor feature drift and retrain if needed
        self.monitor_drift(features)

        # Weight confidence in downstream strategies (placeholder logic)
        adjusted_output = {
            "regime": self.current_regime,
            "confidence": round(self.regime_confidence, 3),
            "drift_score": round(self.last_drift_score, 3),
        }

        # Store telemetry snapshot
        self.telemetry.append(
            {"timestamp": datetime.now(timezone.utc).isoformat(), **adjusted_output}
        )

        return adjusted_output

    # ---------------------------------------------------------------
    # Drift Monitor & Retraining Logic
    # ---------------------------------------------------------------
    def monitor_drift(self, current_features: pd.DataFrame):
        """
        Evaluate the degree of regime drift using DriftMonitor.
        If drift exceeds threshold, initiate background retraining of the regime model.
        """

        if current_features is None or current_features.empty:
            print("⚠️ [MetaAgent] No features provided for drift monitoring.")
            return

        # Step 1 – Compute drift
        try:
            self.last_drift_score = float(
                self.drift_monitor.measure_drift(current_features)
            )
        except Exception as e:
            print(f"❌ [MetaAgent] Drift measurement failed: {e}")
            return

        # Step 2 – Log drift
        print(f"🔍 [MetaAgent] Drift score: {self.last_drift_score:.3f}")

        # Step 3 – Gradual confidence decay for mild drift
        if (
            0.5 * self.drift_monitor.threshold
            < self.last_drift_score
            < self.drift_monitor.threshold
        ):
            self.regime_confidence = max(0.5, self.regime_confidence * 0.9)
            print(f"🟡 [MetaAgent] Confidence reduced to {self.regime_confidence:.2f}")

        # Step 4 – Trigger retraining if drift exceeds threshold
        if self.last_drift_score > self.drift_monitor.threshold and not self.retraining:
            print(
                "⚠️ [MetaAgent] Drift exceeds threshold — initiating retraining sequence."
            )
            self.retraining = True
            self.regime_confidence *= 0.5

            # Spawn background retraining to avoid blocking
            def retrain_task():
                try:
                    print(
                        "🚀 [MetaAgent] Starting asynchronous regime model retraining..."
                    )
                    new_model = train_regime_lstm(
                        features=current_features,
                        save_dir=str(self.model_dir),
                        epochs=15,
                    )

                    # Load updated weights into forecaster
                    self.regime_forecaster.model = new_model
                    self.drift_monitor.ref_stats = (
                        self.drift_monitor.compute_feature_stats(current_features)
                    )
                    self.regime_confidence = 1.0
                    print(
                        "♻️ [MetaAgent] Regime model retraining completed and reloaded successfully."
                    )
                except Exception as e:
                    print(f"❌ [MetaAgent] Retraining failed: {e}")
                finally:
                    self.retraining = False

            threading.Thread(target=retrain_task, daemon=True).start()

    # ---------------------------------------------------------------
    # Telemetry Export
    # ---------------------------------------------------------------
    def export_telemetry(
        self, path: str | Path = "F:/NEXORA/logs/metaagent_telemetry.json"
    ):
        """Save telemetry (drift & confidence history) to disk for analysis."""
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.telemetry, f, indent=2)
            print(f"🧭 Telemetry exported to {path}")
        except Exception as e:
            print(f"❌ Telemetry export failed: {e}")


# --------------------------------------------------------------------
# Diagnostic Entry Point
# --------------------------------------------------------------------
if __name__ == "__main__":
    import numpy as np

    # Simulated data for demonstration
    fake_prices = pd.DataFrame(
        {"AAPL": np.random.rand(300), "GOOG": np.random.rand(300)}
    )

    fake_features = pd.DataFrame(
        {
            "rank": np.random.randn(300),
            "score": np.random.rand(300),
            "vol": np.random.rand(300),
            "spread_mean": np.random.randn(300),
            "spread_std": np.random.rand(300),
        }
    )

    agent = MetaAgent()
    output = agent.evaluate_agents({"prices": fake_prices, "features": fake_features})
    print(json.dumps(output, indent=2))

    agent.export_telemetry()
