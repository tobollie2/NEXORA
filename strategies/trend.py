# strategies/trend.py
# pyright: strict
from __future__ import annotations
from typing import Any, Dict, Optional
import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    Simple moving average crossover trend-following strategy.
    """

    @classmethod
    def parameter_grid(cls) -> Dict[str, list[int]]:
        """Grid search parameter ranges."""
        return {
            "short_window": [10, 20, 30],
            "long_window": [50, 100, 150],
        }

    # ------------------------------------------------------------------
    def generate_signal(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on moving average crossover."""
        if data.empty or "close" not in data.columns:
            return None

        short_val = self.get_param("short_window", 20)
        long_val = self.get_param("long_window", 100)

        # Safe conversions
        short_window = (
            int(short_val) if isinstance(short_val, (int, float, str)) else 20
        )
        long_window = int(long_val) if isinstance(long_val, (int, float, str)) else 100

        df = data.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")  # type: ignore
        df["close"] = df["close"].fillna(method="ffill")  # type: ignore

        # Moving averages
        df["sma_short"] = df["close"].rolling(window=short_window).mean()  # type: ignore
        df["sma_long"] = df["close"].rolling(window=long_window).mean()  # type: ignore
        df.dropna(inplace=True)

        if df.empty:
            return None

        last_short = float(df["sma_short"].iloc[-1])
        last_long = float(df["sma_long"].iloc[-1])
        last_close = float(df["close"].iloc[-1])

        if last_short > last_long:
            side = "BUY"
        elif last_short < last_long:
            side = "SELL"
        else:
            side = "HOLD"

        return {
            "symbol": df.columns.name or "UNKNOWN",
            "side": side,
            "price": last_close,
        }

    # ------------------------------------------------------------------
    def run_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Simplified backtest computing cumulative return."""
        if data.empty or "close" not in data.columns:
            return {"strategy": "TrendFollowing", "total_return": 0.0}

        df = data.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")  # type: ignore
        df["close"] = df["close"].fillna(method="ffill")  # type: ignore

        total_return = 0.0
        if df.shape[0] > 1 and df["close"].iloc[0] != 0:
            total_return = (df["close"].iloc[-1] - df["close"].iloc[0]) / df[
                "close"
            ].iloc[0]

        return {"strategy": "TrendFollowing", "total_return": total_return}
