import pandas as pd
import numpy as np


class MeanReversionStrategy:
    """Basic mean reversion based on z-score."""

    def __init__(self, lookback=20, threshold=2.0):
        self.lookback = lookback
        self.threshold = threshold

    def parameter_grid(self):
        return {"lookback": [10, 20, 30], "threshold": [1.5, 2.0, 2.5]}

    def sample_parameters(self):
        return {
            "lookback": np.random.choice([10, 20, 30]),
            "threshold": np.random.choice([1.5, 2.0, 2.5]),
        }

    def extract_features(self, data):
        return {"volatility": data["returns"].std(), "mean": data["returns"].mean()}

    def run_backtest(self, params, data):
        prices = data["prices"]
        returns = data["returns"].fillna(0)
        rolling_mean = prices.rolling(params["lookback"]).mean()
        rolling_std = prices.rolling(params["lookback"]).std()
        zscore = (prices - rolling_mean) / rolling_std
        signals = (zscore < -params["threshold"]).astype(int) - (
            zscore > params["threshold"]
        ).astype(int)
        pnl = (signals.shift(1) * returns).cumsum().iloc[-1]
        return {"pnl": pnl}

    def parameters(self):
        return {"lookback": self.lookback, "threshold": self.threshold}
