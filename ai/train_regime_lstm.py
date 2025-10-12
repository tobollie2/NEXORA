# /ai/train_regime_lstm.py

"""
NEXORA Regime LSTM Trainer
--------------------------
This script prepares features, trains the RegimeLSTM model,
and saves both the model weights and metadata.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch
from torch import nn, optim

from ai.models.regime_lstm_trainer import (
    RegimeLSTM,
    make_features,
    save_regime_model,
)
from strategies.statistical_arbitrage_cluster import StatisticalArbitrageCluster


# ---------------------------------------------------------------------
# Training Configuration
# ---------------------------------------------------------------------
DATA_DIR = Path("F:/NEXORA/data/cleaned")
MODEL_DIR = Path("F:/NEXORA/ai/models")
DEFAULT_TRAIN_FILE = DATA_DIR / "BTC_USD_1m_cleaned.csv"


# ---------------------------------------------------------------------
# Utility: Load Market Data
# ---------------------------------------------------------------------
def load_market_data(file_path: Path) -> pd.DataFrame:
    """Load market data for training."""
    if not file_path.exists():
        raise FileNotFoundError(f"Missing data file: {file_path}")
    df = pd.read_csv(file_path)
    if "close" not in df.columns:
        raise ValueError("Data file must contain a 'close' column.")
    return df[["close"]]


# ---------------------------------------------------------------------
# Training Routine
# ---------------------------------------------------------------------
def train_regime_lstm_model(
    prices_df: pd.DataFrame,
    cluster_engine: StatisticalArbitrageCluster,
    epochs: int = 20,
    save_dir: Path = MODEL_DIR,
) -> RegimeLSTM:
    """
    Train a RegimeLSTM model using dynamically derived features.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # -----------------------------------------------------------------
    # 1. Build training features
    # -----------------------------------------------------------------
    features: pd.DataFrame = make_features(prices_df, cluster_engine)
    if features.empty:
        raise ValueError("Feature matrix is empty. Cannot train model.")

    # -----------------------------------------------------------------
    # 2. Construct pseudo-regime labels
    # -----------------------------------------------------------------
    y = torch.zeros(len(features), dtype=torch.long)
    y[features["rank"] > 1] = 1
    y[(features["score"] > 0.6) & (features["vol"] < 0.015)] = 2
    y[features["vol"] > features["vol"].quantile(0.8)] = 3

    # -----------------------------------------------------------------
    # 3. Prepare tensors
    # -----------------------------------------------------------------
    X = torch.tensor(features.values, dtype=torch.float32).unsqueeze(0)
    y = y[: X.shape[1]]  # align label length with sequence length

    # -----------------------------------------------------------------
    # 4. Initialize model
    # -----------------------------------------------------------------
    model = RegimeLSTM(input_dim=X.shape[-1])
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    # -----------------------------------------------------------------
    # 5. Train loop
    # -----------------------------------------------------------------
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(X.to(device)).squeeze(0)
        loss = criterion(outputs, y.to(device))
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 5 == 0:
            print(f"[Epoch {epoch + 1}/{epochs}] Loss = {loss.item():.4f}")

    # -----------------------------------------------------------------
    # 6. Save model + metadata
    # -----------------------------------------------------------------
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "regime_lstm.pt"
    save_regime_model(model, save_path)

    print(f"✅ Training complete at {datetime.now(timezone.utc).isoformat()}")
    return model


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Regime LSTM Training Pipeline")

    try:
        # Load market data
        df = load_market_data(DEFAULT_TRAIN_FILE)

        # Initialize cluster engine
        cluster_engine = StatisticalArbitrageCluster(method="engle-granger")

        # Train model
        trained_model = train_regime_lstm_model(df, cluster_engine, epochs=25)

        print("🎯 Regime LSTM training successfully completed.")
    except Exception as e:
        print(f"❌ Training failed: {e}")
        sys.exit(1)
