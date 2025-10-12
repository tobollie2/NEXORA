# backtest/performance_metrics.py

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional


# ============================================================================
# 🔹 Core Performance Metric Utilities
# ============================================================================


def compute_performance_metrics(
    equity_curve: pd.Series, risk_free_rate: float = 0.0
) -> Dict[str, Any]:
    """
    Compute common backtest performance metrics from an equity curve.
    Assumes equity_curve is indexed by date and contains portfolio values.
    """
    returns = equity_curve.pct_change().dropna()

    if len(returns) == 0:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "volatility": 0.0,
            "trades": 0,
        }

    # Basic stats
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    mean_return = returns.mean()
    std_return = returns.std()

    # Annualized Sharpe ratio
    sharpe = (
        np.sqrt(252) * (mean_return - risk_free_rate / 252) / std_return
        if std_return > 0
        else 0.0
    )

    # Sortino ratio (downside deviation)
    downside = returns[returns < 0].std()
    sortino = (
        np.sqrt(252) * (mean_return - risk_free_rate / 252) / downside
        if downside > 0
        else 0.0
    )

    # Max drawdown
    rolling_max = equity_curve.cummax()
    drawdown = equity_curve / rolling_max - 1
    max_dd = drawdown.min()

    # Win rate
    wins = (returns > 0).sum()
    win_rate = wins / len(returns)

    # Volatility (annualized)
    vol = std_return * np.sqrt(252)

    return {
        "total_return": round(float(total_return), 4),
        "sharpe_ratio": round(float(sharpe), 3),
        "sortino_ratio": round(float(sortino), 3),
        "max_drawdown": round(float(max_dd), 4),
        "win_rate": round(float(win_rate), 3),
        "volatility": round(float(vol), 3),
        "trades": int(len(returns)),
    }


# ============================================================================
# 🔹 Report Generator Class
# ============================================================================


class BacktestReportGenerator:
    """
    Generates tabular and HTML reports from backtest results.
    Integrates with BacktestRunner.
    """

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------------------
    def save_html_report(self, df: pd.DataFrame, name: Optional[str] = None):
        """
        Saves the provided DataFrame as an HTML report file.
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            name = f"backtest_report_{timestamp}.html"

        html_path = os.path.join(self.output_dir, name)
        try:
            df.to_html(html_path, index=False, justify="center", border=0)
            print(f"✅ HTML report saved → {html_path}")
        except Exception as e:
            print(f"❌ Failed to save HTML report: {e}")

    # ------------------------------------------------------------------------
    def generate_summary(self, results: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate per-strategy results and compute mean performance metrics.
        """
        if "strategy" not in results.columns:
            print("⚠️ Results missing 'strategy' column; skipping summary aggregation.")
            return results

        summary = (
            results.groupby("strategy")
            .agg(
                {
                    "total_return": "mean",
                    "sharpe_ratio": "mean",
                    "sortino_ratio": "mean",
                    "max_drawdown": "mean",
                    "win_rate": "mean",
                    "volatility": "mean",
                }
            )
            .reset_index()
        )

        summary = summary.round(4)
        summary["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return summary

    # ------------------------------------------------------------------------
    def save_summary_csv(self, summary: pd.DataFrame, name: Optional[str] = None):
        """
        Saves summary metrics as a CSV file for later analysis.
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            name = f"backtest_summary_{timestamp}.csv"

        csv_path = os.path.join(self.output_dir, name)
        try:
            summary.to_csv(csv_path, index=False)
            print(f"📊 Summary CSV saved → {csv_path}")
        except Exception as e:
            print(f"❌ Failed to save CSV summary: {e}")
