# /strategies/trend_following.py
import pandas as pd
import numpy as np


class TrendFollowingStrategy:
    """
    Simple trend-following strategy based on SMA crossover.
    """

    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def parameter_grid(self):
        return {"short_window": [10, 20, 30], "long_window": [50, 100, 200]}

    def sample_parameters(self):
        return {
            "short_window": np.random.choice([10, 20, 30]),
            "long_window": np.random.choice([50, 100, 200]),
        }

    def extract_features(self, data):
        return {"mean": data["prices"].mean(), "std": data["prices"].std()}

    def run_backtest(self, params, data):
        prices = data["prices"]
        short_sma = prices.rolling(params["short_window"]).mean()
        long_sma = prices.rolling(params["long_window"]).mean()
        signals = (short_sma > long_sma).astype(int)
        returns = data["returns"].fillna(0)
        pnl = (signals.shift(1) * returns).cumsum().iloc[-1]
        return {"pnl": pnl}

    def evaluate_signals(self, signals, data):
        returns = data["returns"].fillna(0)
        pnl = (signals.shift(1) * returns).cumsum().iloc[-1]
        return {"pnl": pnl}

    def parameters(self):
        return {"short_window": self.short_window, "long_window": self.long_window}
