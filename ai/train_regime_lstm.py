# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
ai/train_regime_lstm.py
---------------------------------
Automated training script for the RegimeLSTM forecaster.
This script regenerates features, trains the model if needed,
and validates the saved model signature and metadata.
"""

import os
import pandas as pd
import sys
from pathlib import Path

# ensure project root is visible to the interpreter
sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone
import torch

# Local imports
from ai.models.regime_lstm_trainer import (
    make_features,
    train_regime_lstm,
    load_regime_model,
)
from ai.models.regime_lstm_trainer import save_regime_model
from ai.models.regime_drift_monitor import DriftMonitor


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
DATA_PATH = Path("F:/NEXORA/data/cleaned/market_data.csv")  # Example input
SAVE_DIR = Path("F:/NEXORA/ai/models")
FEATURE_PATH = SAVE_DIR / "regime_features.csv"
MODEL_PATH = SAVE_DIR / "regime_lstm.pt"
REBUILD = False  # Set to True to force retraining
CLUSTER_ENGINE = None  # optional placeholder for cointegration clustering


def should_retrain(model_path: Path, feature_path: Path) -> bool:
    """Decide whether retraining is required."""
    if not model_path.exists():
        print("⚠️ No existing model found — retraining required.")
        return True
    if not feature_path.exists():
        print("⚠️ Feature file missing — retraining required.")
        return True

    # Compare timestamps
    model_time = datetime.fromtimestamp(model_path.stat().st_mtime, tz=timezone.utc)
    feat_time = datetime.fromtimestamp(feature_path.stat().st_mtime, tz=timezone.utc)
    if feat_time > model_time:
        print("🔁 Feature file is newer than model — retraining.")
        return True

    print("✅ Existing model appears current. Skipping retrain.")
    return False


def main():
    """Main entry point for RegimeLSTM training workflow."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Load or generate features
    if not FEATURE_PATH.exists():
        print("🧮 Generating features...")
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Missing input data at {DATA_PATH}")
        prices_df = pd.read_csv(DATA_PATH, index_col=0)
        features = make_features(prices_df, cluster_engine=CLUSTER_ENGINE)
        features.to_csv(FEATURE_PATH, index=False)
        print(f"✅ Saved features → {FEATURE_PATH}")
    else:
        features = pd.read_csv(FEATURE_PATH)
        # ------------------------------------------------------------------


# Drift validation after training or loading
# ------------------------------------------------------------------
drift_monitor = DriftMonitor(MODEL_PATH.with_suffix(".meta.json"), threshold=0.25)

if drift_monitor.has_drifted(features):
    print("⚠️ Significant feature drift detected → retraining model.")
    model = train_regime_lstm(features, save_dir=str(SAVE_DIR), epochs=15)
else:
    print("✅ No significant drift detected. Model stable.")

    print(f"📂 Loaded existing features ({len(features)} rows)")

    # Check model freshness
    retrain = should_retrain(MODEL_PATH, FEATURE_PATH) or REBUILD

    if retrain:
        print("🚀 Beginning RegimeLSTM training process...")
        model = train_regime_lstm(features, save_dir=str(SAVE_DIR), epochs=15)

    else:
        print("📦 Loading existing model...")
        model = load_regime_model(MODEL_PATH)

    # Post-validation of model metadata
    print("\n🔍 Model signature check:")
    meta = save_regime_model(model, str(MODEL_PATH))

    print(f"✅ Metadata confirmed: {meta}")


if __name__ == "__main__":
    main()
