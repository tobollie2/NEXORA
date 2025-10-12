# /monitoring/live_logger.py
import logging
import time
from datetime import datetime

import pandas as pd
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class LiveLogger:
    """Real-time monitoring and visualization of live trading state."""

    def __init__(self, report_path="reports/live_metrics.csv"):
        self.console = Console()
        self.report_path = report_path
        self.metrics_history = []
        self.start_time = time.time()
        self.trade_count = 0
        self.logger = logging.getLogger("LiveLogger")
        self.logger.setLevel(logging.INFO)

    def update(self, snapshot: dict, last_trade: dict | None = None):
        """Update live metrics and optionally log to file."""
        uptime = time.time() - self.start_time
        pnl = snapshot.get("unrealized_pnl", 0.0)
        balance = snapshot.get("balance", 0.0)
        positions = snapshot.get("positions", {})
        ts = snapshot.get("timestamp", datetime.utcnow().isoformat())

        if last_trade:
            self.trade_count += 1
            last_symbol = last_trade["symbol"]
            last_price = last_trade["executed_price"]
        else:
            last_symbol = "-"
            last_price = "-"

        # Prepare console table
        table = Table(title=f"NEXORA Live Monitor — {ts}")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="bold white")

        table.add_row("Uptime (s)", f"{uptime:,.1f}")
        table.add_row("Trades Executed", str(self.trade_count))
        table.add_row("Account Balance", f"${balance:,.2f}")
        table.add_row("Unrealized PnL", f"${pnl:,.2f}")
        table.add_row("Last Symbol", str(last_symbol))
        table.add_row("Last Price", str(last_price))

        pos_str = (
            "\n".join([f"{k}: {v['size']} @ {v['avg_price']:.2f}" for k, v in positions.items()])
            or "No Open Positions"
        )
        panel = Panel(pos_str, title="Current Positions", border_style="green")

        with Live(auto_refresh=False, console=self.console, refresh_per_second=2) as live:
            live.update(Panel(table, title="System Metrics", border_style="blue"))
            live.update(panel)
            live.refresh()

        # Record metrics for later visualization
        record = {
            "timestamp": ts,
            "balance": balance,
            "pnl": pnl,
            "trade_count": self.trade_count,
            "positions": len(positions),
        }
        self.metrics_history.append(record)

        # Periodically flush to CSV
        if len(self.metrics_history) % 10 == 0:
            pd.DataFrame(self.metrics_history).to_csv(self.report_path, index=False)
            self.logger.info(f"Metrics logged → {self.report_path}")
