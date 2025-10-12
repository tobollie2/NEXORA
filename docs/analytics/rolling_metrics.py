from typing import Optional

import numpy as np
import pandas as pd


class RollingMetrics:
    """Compute rolling performance metrics for backtest results."""

    def __init__(self, window: int = 30):
        self.window = window

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"equity_curve", "returns"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing columns in DataFrame: {required_cols - set(df.columns)}")

        df = df.copy()

        # Rolling volatility
        df["rolling_volatility"] = df["returns"].rolling(self.window).std(ddof=0)

        # Rolling Sharpe Ratio
        rolling_mean = df["returns"].rolling(self.window).mean()
        rolling_std = df["returns"].rolling(self.window).std(ddof=0)
        df["rolling_sharpe"] = np.where(rolling_std != 0, rolling_mean / rolling_std, np.nan)

        # Rolling Maximum Drawdown
        df["cummax"] = df["equity_curve"].cummax()
        df["drawdown"] = df["equity_curve"] / df["cummax"] - 1
        df["rolling_max_drawdown"] = df["drawdown"].rolling(self.window).min()

        # Rolling Trade Count (optional)
        if "trade_count" in df.columns:
            df["rolling_trade_count"] = df["trade_count"].rolling(self.window).sum()

        # Clean up helper columns
        df.drop(columns=["cummax", "drawdown"], inplace=True, errors="ignore")

        return df

    @staticmethod
    def summary(df: pd.DataFrame) -> pd.DataFrame:
        metrics = ["rolling_sharpe", "rolling_volatility", "rolling_max_drawdown"]
        available = [m for m in metrics if m in df.columns]
        summary = df[available].describe(percentiles=[0.05, 0.5, 0.95]).T
        summary.rename(columns={"50%": "median"}, inplace=True)
        return summary


if __name__ == "__main__":
    # Example demo run
    np.random.seed(42)
    demo = pd.DataFrame(
        {
            "timestamp": pd.date_range(start="2024-01-01", periods=300, freq="D"),
            "returns": np.random.normal(0.001, 0.02, 300),
        }
    )
    demo["equity_curve"] = (1 + demo["returns"]).cumprod()

    metrics = RollingMetrics(window=30)
    demo_out = metrics.compute(demo)
    print(metrics.summary(demo_out))
