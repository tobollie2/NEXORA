import os

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from analytics.rolling_metrics import RollingMetrics


class BacktestReportGenerator:
    """Generates interactive HTML reports from backtest results with rolling analytics."""

    def __init__(self, output_dir: str = "reports", window: int = 30):
        self.output_dir = output_dir
        self.metrics_engine = RollingMetrics(window=window)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_html_report(self, df: pd.DataFrame, strategy_name: str, asset: str) -> str:
        # Compute rolling metrics
        df = self.metrics_engine.compute(df)
        summary_df = self.metrics_engine.summary(df)

        # --- Build Subplots Layout ---
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(
                f"{strategy_name} | {asset} — Equity Curve",
                "Rolling Sharpe Ratio",
                "Rolling Volatility",
                "Rolling Max Drawdown",
            ),
        )

        # Equity curve
        fig.add_trace(
            go.Scatter(x=df.index, y=df["equity_curve"], name="Equity Curve", mode="lines"),
            row=1,
            col=1,
        )

        # Rolling Sharpe
        if "rolling_sharpe" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["rolling_sharpe"],
                    name="Rolling Sharpe",
                    mode="lines",
                ),
                row=2,
                col=1,
            )

        # Rolling Volatility
        if "rolling_volatility" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["rolling_volatility"],
                    name="Rolling Volatility",
                    mode="lines",
                ),
                row=3,
                col=1,
            )

        # Rolling Max Drawdown
        if "rolling_max_drawdown" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["rolling_max_drawdown"],
                    name="Rolling Drawdown",
                    mode="lines",
                ),
                row=4,
                col=1,
            )

        # Layout aesthetics
        fig.update_layout(
            title=f"Performance Report: {strategy_name} ({asset})",
            height=1000,
            showlegend=True,
            template="plotly_white",
        )

        # --- Add summary table ---
        summary_table = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Metric", "Mean", "Median", "Std", "5th %", "95th %"],
                        fill_color="lightgrey",
                        align="center",
                    ),
                    cells=dict(
                        values=[
                            summary_df.index,
                            summary_df["mean"].round(4),
                            summary_df["median"].round(4),
                            summary_df["std"].round(4),
                            summary_df["5%"].round(4),
                            summary_df["95%"].round(4),
                        ],
                        align="center",
                    ),
                )
            ]
        )

        # Save to HTML
        output_path = os.path.join(self.output_dir, f"{strategy_name}_{asset}_report.html")
        pio.write_html(
            fig,
            file=output_path,
            include_plotlyjs="cdn",
            full_html=True,
            auto_open=False,
        )

        # Append summary table HTML
        summary_html = pio.to_html(summary_table, include_plotlyjs=False, full_html=False)
        with open(output_path, "a", encoding="utf-8") as f:
            f.write("<h3>Summary Statistics</h3>" + summary_html)

        return output_path


if __name__ == "__main__":
    import numpy as np

    np.random.seed(42)
    df_demo = pd.DataFrame(
        {
            "returns": np.random.normal(0.001, 0.02, 300),
        }
    )
    df_demo["equity_curve"] = (1 + df_demo["returns"]).cumprod()
    df_demo.index = pd.date_range(start="2024-01-01", periods=len(df_demo), freq="D")

    gen = BacktestReportGenerator()
    path = gen.generate_html_report(df_demo, strategy_name="TrendFollowing", asset="BTCUSD")
    print(f"Report saved to: {path}")
