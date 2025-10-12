# File: data/feature_store.py

import numpy as np
import pandas as pd


class FeatureStore:
    """
    Transforms raw OHLCV data from the DataIngestion feed
    into structured features for regime detection and strategy logic.
    """

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.config = config or {}
        self.lookback = self.config.get("feature_lookback", 100)
        self.features = pd.DataFrame()

    def compute_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """
        Compute rolling statistical and technical features.
        Input:
            ohlcv (pd.DataFrame): recent price history from DataIngestion
        Output:
            pd.DataFrame: most recent row of features
        """
        if len(ohlcv) < 5:
            return pd.DataFrame()

        df = ohlcv.copy()
        df["returns"] = df["close"].pct_change()
        df["log_ret"] = np.log(df["close"] / df["close"].shift(1))

        # --- Rolling volatility ---
        df["volatility_10"] = df["returns"].rolling(window=10).std()
        df["volatility_50"] = df["returns"].rolling(window=50).std()

        # --- Rolling momentum (drift indicator) ---
        df["momentum_10"] = df["close"] / df["close"].shift(10) - 1
        df["momentum_50"] = df["close"] / df["close"].shift(50) - 1

        # --- Moving averages ---
        df["sma_10"] = df["close"].rolling(10).mean()
        df["sma_50"] = df["close"].rolling(50).mean()

        # --- Moving average slope (trend strength) ---
        df["slope_10"] = df["sma_10"].diff()
        df["slope_50"] = df["sma_50"].diff()

        # --- Volume features ---
        df["vol_mean_20"] = df["volume"].rolling(20).mean()
        df["vol_ratio"] = df["volume"] / df["vol_mean_20"]

        # --- Z-score of returns (normalized drift) ---
        df["zscore_ret"] = (df["returns"] - df["returns"].rolling(50).mean()) / df[
            "returns"
        ].rolling(50).std()

        # Drop NaN and keep only last row for live use
        df = df.dropna().reset_index(drop=True)
        latest = df.tail(1).copy()
        self.features = latest

        if self.logger:
            self.logger.info(f"Computed features at {latest['timestamp'].iloc[0]}")

        return latest

    def get_features(self) -> dict:
        """Return current feature snapshot as dict for ML input."""
        return self.features.to_dict("records")[0] if not self.features.empty else {}

    def get_feature_names(self):
        """List all current feature column names."""
        return list(self.features.columns) if not self.features.empty else []
