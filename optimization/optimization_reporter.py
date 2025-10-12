import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from plotly.subplots import make_subplots


class OptimizationReporter:
    """Generates comparative visualization dashboards for optimization results."""

    def __init__(self, reports_dir="reports/optimization"):
        self.reports_dir = reports_dir
        self.visual_dir = os.path.join(reports_dir, "visuals")
        os.makedirs(self.visual_dir, exist_ok=True)

    def load_logs(self):
        logs = []
        for file in os.listdir(self.reports_dir):
            if file.endswith("_log.csv"):
                df = pd.read_csv(os.path.join(self.reports_dir, file))
                df["file"] = file
                logs.append(df)
        return pd.concat(logs, ignore_index=True) if logs else pd.DataFrame()

    def plot_convergence(self, df, strategy):
        df = df.copy()
        df["iteration"] = range(1, len(df) + 1)
        fig = px.line(
            df,
            x="iteration",
            y="score",
            title=f"Convergence — {strategy}",
            markers=True,
        )
        fig.update_layout(template="plotly_white", height=400)
        return fig

    def plot_parameter_heatmap(self, df, param_x, param_y):
        if param_x not in df.columns or param_y not in df.columns:
            return None
        pivot = df.pivot_table(index=param_y, columns=param_x, values="score", aggfunc="mean")
        fig = px.imshow(
            pivot,
            title=f"Performance Surface: {param_x} vs {param_y}",
            labels=dict(color="Score"),
            aspect="auto",
        )
        fig.update_layout(template="plotly_white", height=500)
        return fig

    def plot_engine_comparison(self, summary_df):
        fig = px.bar(
            summary_df,
            x="strategy",
            y="best_score",
            color="engine",
            barmode="group",
            title="Best Scores per Engine",
        )
        fig.update_layout(template="plotly_white", height=400)
        return fig

    def generate_html_dashboard(self):
        summary_path = os.path.join(self.reports_dir, "optimization_summary.csv")
        if not os.path.exists(summary_path):
            print("No optimization summary found.")
            return None

        summary_df = pd.read_csv(summary_path)
        logs_df = self.load_logs()
        if logs_df.empty:
            print("No detailed logs found.")
            return None

        html_blocks = []

        # Per-strategy convergence & surfaces
        for strat in summary_df["strategy"].unique():
            df_sub = logs_df[logs_df["file"].str.contains(strat)]
            fig_conv = self.plot_convergence(df_sub, strat)
            html_blocks.append(fig_conv.to_html(full_html=False, include_plotlyjs="cdn"))

            cols = [c for c in df_sub.columns if c not in ["score", "file"]]
            if len(cols) >= 2:
                fig_heat = self.plot_parameter_heatmap(df_sub, cols[0], cols[1])
                if fig_heat:
                    html_blocks.append(fig_heat.to_html(full_html=False, include_plotlyjs=False))

        # Global comparison
        fig_comp = self.plot_engine_comparison(summary_df)
        html_blocks.append(fig_comp.to_html(full_html=False, include_plotlyjs=False))

        # Write final dashboard
        out_path = os.path.join(self.visual_dir, "optimization_dashboard.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("<h1>NEXORA Optimization Dashboard</h1>" + "".join(html_blocks))
        print(f"Dashboard generated → {out_path}")
        return out_path


if __name__ == "__main__":
    reporter = OptimizationReporter()
    reporter.generate_html_dashboard()
