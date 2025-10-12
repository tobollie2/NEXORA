# /ai/regime_detector.py
import numpy as np
import pandas as pd


class MarketRegimeDetector:
    """
    Detects current market regime using volatility, momentum, and correlation metrics.
    """

    def __init__(self, lookback=200):
        self.lookback = lookback
        self.current_regime = "neutral"

    def compute_features(self, price_series: pd.Series) -> dict:
        returns = price_series.pct_change().dropna()
        vol = returns.rolling(20).std().iloc[-1]
        mom = price_series.pct_change(20).iloc[-1]
        kurt = returns.kurtosis()
        skew = returns.skew()
        return {"vol": vol, "mom": mom, "kurt": kurt, "skew": skew}

    def classify_regime(self, features: dict) -> str:
        vol, mom, kurt = features["vol"], features["mom"], features["kurt"]

        if vol > 0.04 and kurt > 3:
            regime = "volatile"
        elif mom > 0.02:
            regime = "trending"
        elif mom < -0.02:
            regime = "bearish_trend"
        elif vol < 0.01 and abs(mom) < 0.005:
            regime = "calm"
        else:
            regime = "mean_reverting"

        self.current_regime = regime
        return regime

    def detect(self, price_series: pd.Series) -> str:
        features = self.compute_features(price_series)
        regime = self.classify_regime(features)
        return regime
