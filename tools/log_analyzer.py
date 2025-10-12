import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import seaborn as sns
import numpy as np


class NEXORAAnalyzer:
    """
    Advanced analytics for post-trade performance review.
    Includes per-symbol, per-strategy, rolling metrics, and correlation analysis.
    """

    def __init__(self, logs_path="logs/trades.csv", report_dir="logs/reports"):
        self.logs_path = Path(logs_path)
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.df = None
        print("📊 NEXORA Analyzer initialized.")

    # -------------------------------------------------------------
    def load_trades(self):
        """Load trade log file."""
        if not self.logs_path.exists():
            print("⚠️ No trade log file found.")
            return False

        self.df = pd.read_csv(self.logs_path, parse_dates=["timestamp"])
        expected_cols = {"timestamp", "symbol", "strategy", "pnl"}
        missing = expected_cols - set(self.df.columns)
        if missing:
            print(f"⚠️ Missing columns: {missing}")

        print(f"✅ Loaded {len(self.df)} trades from {self.logs_path}")
        return True

    # -------------------------------------------------------------
    def compute_metrics(self):
        """Compute overall and per-category performance metrics."""
        if self.df is None or self.df.empty:
            print("⚠️ No data available for analysis.")
            return {}

        total_trades = len(self.df)
        total_pnl = self.df["pnl"].sum()
        avg_pnl = self.df["pnl"].mean()
        win_rate = (self.df["pnl"] > 0).mean() * 100
        best_trade = self.df["pnl"].max()
        worst_trade = self.df["pnl"].min()

        # Strategy-level
        strategy_perf = (
            self.df.groupby("strategy")["pnl"]
            .agg(["count", "sum", "mean"])
            .sort_values("sum", ascending=False)
        )

        # Symbol-level
        symbol_perf = (
            self.df.groupby("symbol")["pnl"]
            .agg(["count", "sum", "mean"])
            .sort_values("sum", ascending=False)
        )
        symbol_perf["win_rate"] = (
            self.df.groupby("symbol")["pnl"].apply(lambda x: (x > 0).mean() * 100)
        )

        metrics = {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "win_rate": win_rate,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "strategy_perf": strategy_perf,
            "symbol_perf": symbol_perf,
        }

        print(f"📈 {total_trades} trades | Win Rate {win_rate:.2f}% | Total PnL ${total_pnl:.2f}")
        return metrics

    # -------------------------------------------------------------
    def compute_rolling_metrics(self, window=30):
        """Compute rolling Sharpe ratio, drawdown, and volatility."""
        if self.df is None or self.df.empty:
            return None

        df = self.df.copy()
        df["cum_pnl"] = df["pnl"].cumsum()

        # Rolling volatility
        df["rolling_volatility"] = df["pnl"].rolling(window).std()

        # Rolling Sharpe
        rolling_mean = df["pnl"].rolling(window).mean()
        df["rolling_sharpe"] = np.where(
            df["rolling_volatility"] != 0,
            rolling_mean / df["rolling_volatility"],
            np.nan,
        )

        # Rolling drawdown
        rolling_max = df["cum_pnl"].rolling(window, min_periods=1).max()
        df["rolling_drawdown"] = (df["cum_pnl"] - rolling_max) / rolling_max * 100

        print(f"📉 Computed rolling metrics (window={window}).")
        return df

    # -------------------------------------------------------------
    def plot_rolling_metrics(self, df):
        """Plot rolling Sharpe ratio, volatility, and drawdown."""
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        axes[0].plot(df["timestamp"], df["rolling_sharpe"], color="tab:blue")
        axes[0].set_title("Rolling Sharpe Ratio (30-trade window)")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(df["timestamp"], df["rolling_volatility"], color="tab:orange")
        axes[1].set_title("Rolling Volatility (σ)")
        axes[1].grid(True, alpha=0.3)

        axes[2].plot(df["timestamp"], df["rolling_drawdown"], color="tab:red")
        axes[2].set_title("Rolling Drawdown (%)")
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        path = self.report_dir / "rolling_metrics.png"
        plt.savefig(path)
        plt.close()
        print(f"📉 Rolling metrics chart saved: {path}")
        return path

    # -------------------------------------------------------------
    def plot_equity_curve(self):
        """Plot cumulative equity curve."""
        self.df["cum_pnl"] = self.df["pnl"].cumsum()
        plt.figure(figsize=(10, 5))
        plt.plot(self.df["timestamp"], self.df["cum_pnl"], color="tab:blue", linewidth=2)
        plt.title("NEXORA Cumulative Equity Curve")
        plt.xlabel("Time")
        plt.ylabel("Cumulative PnL ($)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        path = self.report_dir / "equity_curve.png"
        plt.savefig(path)
        plt.close()
        print(f"📈 Equity curve saved: {path}")
        return path

    # -------------------------------------------------------------
    def plot_pnl_distribution(self):
        """Plot trade PnL distribution."""
        plt.figure(figsize=(8, 4))
        sns.histplot(self.df["pnl"], bins=25, kde=True, color="tab:green", alpha=0.7)
        plt.title("Trade PnL Distribution")
        plt.xlabel("PnL ($)")
        plt.ylabel("Frequency")
        plt.tight_layout()
        path = self.report_dir / "pnl_distribution.png"
        plt.savefig(path)
        plt.close()
        print(f"📊 PnL distribution saved: {path}")
        return path

    # -------------------------------------------------------------
    def plot_strategy_correlation(self):
        """Plot correlation heatmap between strategy PnL series."""
        if "strategy" not in self.df.columns:
            print("⚠️ Strategy column missing, cannot compute correlation.")
            return None

        pivot = self.df.pivot_table(index="timestamp", columns="strategy", values="pnl", aggfunc="sum").fillna(0)
        corr = pivot.corr()

        plt.figure(figsize=(7, 5))
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, fmt=".2f")
        plt.title("Strategy PnL Correlation Heatmap")
        plt.tight_layout()
        path = self.report_dir / "strategy_correlation.png"
        plt.savefig(path)
        plt.close()

        print(f"🧠 Strategy correlation heatmap saved: {path}")
        return path

    # -------------------------------------------------------------
    def generate_html_report(self, metrics):
        """Generate HTML report."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        html_path = self.report_dir / f"nexora_trade_report_{timestamp}.html"

        strat_html = metrics["strategy_perf"].to_html(classes="data", border=0)
        symbol_html = metrics["symbol_perf"].to_html(classes="data", border=0)

        html = f"""
        <html>
        <head>
            <title>NEXORA Trade Report</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                h1, h2 {{ color: #4CAF50; }}
                table.data {{ border-collapse: collapse; width: 70%; }}
                table.data th, table.data td {{ border: 1px solid #ccc; padding: 6px; }}
                img {{ margin-bottom: 20px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <h1>📊 NEXORA Trade Analytics Report</h1>
            <p><b>Total Trades:</b> {metrics['total_trades']}</p>
            <p><b>Win Rate:</b> {metrics['win_rate']:.2f}%</p>
            <p><b>Total PnL:</b> ${metrics['total_pnl']:.2f}</p>
            <p><b>Avg PnL:</b> ${metrics['avg_pnl']:.2f}</p>

            <h2>Performance Charts</h2>
            <img src='equity_curve.png' width='700'><br>
            <img src='pnl_distribution.png' width='700'><br>
            <img src='rolling_metrics.png' width='700'><br>
            <img src='strategy_correlation.png' width='700'><br>

            <h2>Strategy Performance</h2>
            {strat_html}

            <h2>Symbol Performance</h2>
            {symbol_html}

            <p style='margin-top:30px;'>Generated on {timestamp}</p>
        </body>
        </html>
        """

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML report saved: {html_path}")
        return html_path

    # -------------------------------------------------------------
    def run_full_analysis(self):
        """Full analytics workflow."""
        if not self.load_trades():
            return

        metrics = self.compute_metrics()
        df_rolling = self.compute_rolling_metrics(window=30)

        self.plot_equity_curve()
        self.plot_pnl_distribution()
        self.plot_rolling_metrics(df_rolling)
        self.plot_strategy_correlation()
        self.generate_html_report(metrics)

        print("🎯 Advanced analytics (with correlation) completed successfully.")


# -------------------------------------------------------------
if __name__ == "__main__":
    analyzer = NEXORAAnalyzer()
    analyzer.run_full_analysis()
