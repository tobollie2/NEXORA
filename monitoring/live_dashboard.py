# /monitoring/live_dashboard.py
import os
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

METRICS_FILE = "reports/live_metrics.csv"
TRADES_FILE = "reports/live_trades.csv"

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "NEXORA Live Dashboard"


def load_data():
    """Safely load metrics and trades data."""
    metrics = (
        pd.read_csv(METRICS_FILE) if os.path.exists(METRICS_FILE) else pd.DataFrame()
    )
    trades = pd.read_csv(TRADES_FILE) if os.path.exists(TRADES_FILE) else pd.DataFrame()
    return metrics, trades


app.layout = html.Div(
    [
        html.H1("🧠 NEXORA Live Dashboard", style={"textAlign": "center"}),
        # Live KPIs
        html.Div(
            id="kpi-container",
            style={"display": "flex", "justifyContent": "space-around"},
        ),
        # Live charts
        dcc.Graph(id="equity-chart"),
        dcc.Graph(id="pnl-chart"),
        # Trade log table
        html.H3("Recent Trades"),
        dash_table.DataTable(
            id="trade-table",
            style_table={"overflowX": "auto"},
            page_size=10,
            style_cell={"textAlign": "center"},
        ),
        # Auto-refresh every 5 seconds
        dcc.Interval(id="interval-component", interval=5000, n_intervals=0),
    ]
)


@app.callback(
    [
        Output("kpi-container", "children"),
        Output("equity-chart", "figure"),
        Output("pnl-chart", "figure"),
        Output("trade-table", "data"),
        Output("trade-table", "columns"),
    ],
    Input("interval-component", "n_intervals"),
)
def update_dashboard(n):
    metrics, trades = load_data()

    # --- KPIs ---
    if not metrics.empty:
        latest = metrics.iloc[-1]
        balance = f"${latest['balance']:,.2f}"
        pnl = f"${latest['pnl']:,.2f}"
        trade_count = int(latest["trade_count"])
        positions = int(latest["positions"])
    else:
        balance, pnl, trade_count, positions = "-", "-", 0, 0

    kpis = [
        html.Div([html.H4("Account Balance"), html.P(balance)]),
        html.Div([html.H4("Unrealized PnL"), html.P(pnl)]),
        html.Div([html.H4("Trades Executed"), html.P(str(trade_count))]),
        html.Div([html.H4("Open Positions"), html.P(str(positions))]),
    ]

    # --- Equity Chart ---
    if not metrics.empty:
        fig_eq = px.line(
            metrics,
            x="timestamp",
            y="balance",
            title="Equity Curve",
            template="plotly_white",
        )
    else:
        fig_eq = px.line(title="Equity Curve (no data yet)")

    # --- PnL Chart ---
    if not metrics.empty:
        fig_pnl = px.line(
            metrics,
            x="timestamp",
            y="pnl",
            title="Unrealized PnL",
            template="plotly_white",
        )
    else:
        fig_pnl = px.line(title="PnL (no data yet)")

    # --- Trades Table ---
    if not trades.empty:
        trades_display = trades.tail(20).iloc[::-1]
        columns = [{"name": c, "id": c} for c in trades_display.columns]
        data = trades_display.to_dict("records")
    else:
        columns, data = [], []

    return kpis, fig_eq, fig_pnl, data, columns


if __name__ == "__main__":
    print("🌐 Launching NEXORA Live Dashboard at http://127.0.0.1:8050")
    app.run_server(debug=True)
