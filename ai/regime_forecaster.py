# ai/regime_forecaster.py

import numpy as np
import pandas as pd
from typing import Union
from ai.models.regime_lstm_trainer import load_regime_model


class RegimeForecaster:
    """
    Predicts the current market regime using a trained LSTM model.
    Supports input from pandas DataFrames, numpy arrays, or lists.
    Returns one of: ["bull", "bear", "sideways", "unknown"].
    """

    def __init__(self, model_path, model_meta_path=None):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            self.model = load_regime_model(self.model_path)
            print(f"✅ Regime model loaded from {self.model_path}")
        except Exception as e:
            print(f"⚠️ Could not load regime model: {e}")
            self.model = None

    def predict_regime(
        self, prices: Union[pd.DataFrame, np.ndarray, list, pd.Series]
    ) -> str:
        """
        Predicts the current regime from price data.
        Handles multiple input types safely and returns a string label.
        """
        # Handle None input
        if prices is None:
            print("⚠️ Received None for 'prices'; returning 'unknown'.")
            return "unknown"

        # Normalize input type
        if isinstance(prices, (list, np.ndarray)):
            prices = pd.DataFrame(prices, columns=["price"])
        elif isinstance(prices, pd.Series):
            prices = pd.DataFrame(prices, columns=["price"])
        elif not isinstance(prices, pd.DataFrame):
            print(f"⚠️ Unexpected type {type(prices)} for prices; returning 'unknown'.")
            return "unknown"

        # Require minimum data points
        if len(prices) < 20:
            print("⚠️ Insufficient data for regime prediction; returning 'unknown'.")
            return "unknown"

        if self.model is None:
            print("⚠️ No regime model loaded; returning 'unknown'.")
            return "unknown"

        # Extract normalized input
        values = prices.values[-60:]  # last 60 timesteps (LSTM input window)
        values = (values - np.mean(values)) / (np.std(values) + 1e-6)

        # Predict regime
        try:
            with np.errstate(all="ignore"):
                pred = self.model.predict(values)
                pred_label = int(np.argmax(pred, axis=-1))

            regime_map = {0: "bear", 1: "sideways", 2: "bull"}
            return regime_map.get(pred_label, "unknown")

        except Exception as e:
            print(f"⚠️ Regime prediction failed: {e}")
            return "unknown"
