import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim


# ---------------------------------------------------------------------
# LSTM Model Definition
# ---------------------------------------------------------------------
class RegimeLSTM(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=64, num_layers=2, output_dim=4, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, dropout=dropout, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out)
        return self.softmax(out)


# ---------------------------------------------------------------------
# Feature Extraction Utility
# ---------------------------------------------------------------------
def make_features(prices_df: pd.DataFrame, cluster_engine=None) -> pd.DataFrame:
    """
    Generates temporal features for regime classification from raw price data.

    Features include:
      - Cointegration rank (if cluster_engine provided)
      - Cluster confidence (if cluster_engine provided)
      - Rolling volatility
      - Rolling mean spread and standard deviation
      - Rolling correlation
    """
    if prices_df is None or prices_df.empty:
        raise ValueError("❌ prices_df cannot be None or empty")

    feats = []
    window_size = 200

    for i in range(window_size, len(prices_df)):
        window = prices_df.iloc[i - window_size : i]

        # Cointegration/cluster results if available
        if cluster_engine is not None and hasattr(cluster_engine, "evaluate_cluster"):
            res = cluster_engine.evaluate_cluster(window)
            rank = res.get("rank", 0)
            score = res.get("score", 0.0)
        else:
            rank, score = 0, 0.0

        # Rolling stats
        vol = window.pct_change().std().mean()
        mean_spread = (window.iloc[:, 0] - window.mean(axis=1)).mean()
        std_spread = (window.iloc[:, 0] - window.mean(axis=1)).std()
        corr = window.corr().mean().mean()

        feats.append([rank, score, vol, mean_spread, std_spread, corr])

    feat_df = pd.DataFrame(
        feats, columns=["rank", "score", "vol", "spread_mean", "spread_std", "corr"]
    ).dropna()

    print(f"✅ Generated {len(feat_df)} feature rows from {len(prices_df)} input samples.")
    return feat_df


# ---------------------------------------------------------------------
# Metadata + Signature Utilities
# ---------------------------------------------------------------------
def compute_model_signature(model: torch.nn.Module) -> str:
    """Return a short, reproducible architecture signature hash."""
    sig = [f"{name}:{tuple(param.shape)}" for name, param in model.named_parameters()]
    return hashlib.md5("".join(sig).encode()).hexdigest()


def save_regime_model(model: torch.nn.Module, path: str | Path):
    """Save model weights and metadata (.meta.json)."""
    path = Path(path)
    meta_path = path.with_suffix(".meta.json")

    torch.save(model.state_dict(), path)

    meta = {
        "signature": compute_model_signature(model),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "torch_version": torch.__version__,
        "input_dim": getattr(model.lstm, "input_size", None),
        "hidden_dim": getattr(model.lstm, "hidden_size", None),
        "num_layers": getattr(model.lstm, "num_layers", None),
        "output_dim": getattr(model.fc, "out_features", None),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"✅ Model + metadata saved → {path}")
    return meta


def load_regime_model(path: str | Path):
    """Load model and validate metadata signature if available."""
    path = Path(path)
    meta_path = path.with_suffix(".meta.json")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = RegimeLSTM()
    model.load_state_dict(torch.load(path, map_location=device))
    model.to(device)

    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        current_sig = compute_model_signature(model)
        if meta.get("signature") != current_sig:
            print("⚠️ Warning: Model architecture signature mismatch!")
        else:
            print("✅ Signature verified successfully.")
    else:
        print("⚠️ No metadata found for this model.")

    return model


# ---------------------------------------------------------------------
# Training Routine
# ---------------------------------------------------------------------
def train_regime_lstm(
    features: pd.DataFrame,
    save_dir="F:/NEXORA/ai/models",
    epochs: int = 20,
    lr: float = 1e-3,
):
    """
    Train a RegimeLSTM model using the provided features.
    Creates synthetic regime labels and saves the trained model + metadata.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Sanity check
    if features is None or features.empty:
        raise ValueError("❌ 'features' cannot be empty for training")

    # Create synthetic labels as placeholders
    y = np.zeros(len(features))
    y[features["rank"] > 1] = 1
    y[(features["score"] > 0.6) & (features["vol"] < 0.015)] = 2
    y[features["vol"] > features["vol"].quantile(0.8)] = 3

    X = torch.tensor(features.values, dtype=torch.float32).unsqueeze(0)
    y = torch.tensor(y, dtype=torch.long)

    model = RegimeLSTM(input_dim=X.shape[-1])
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    print(f"🚀 Training RegimeLSTM for {epochs} epochs on {device}...")

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        outputs = model(X.to(device)).squeeze(0)
        y_aligned = y[: outputs.shape[0]]  # Align shapes if needed
        loss = criterion(outputs, y_aligned.to(device))
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
            print(f"  Epoch {epoch+1}/{epochs} | Loss={loss.item():.4f}")

    # Save model + metadata
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    model_path = Path(save_dir) / "regime_lstm.pt"
    meta = save_regime_model(model, model_path)

    print(f"✅ Model training complete. Saved to: {model_path}")
    print(f"🧠 Metadata: {meta}")
    return model


__all__ = [
    "RegimeLSTM",
    "make_features",
    "train_regime_lstm",
    "save_regime_model",
    "load_regime_model",
]
