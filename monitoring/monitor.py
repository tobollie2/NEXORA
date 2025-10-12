import asyncio

from rich.console import Console
from rich.table import Table


class LiveMonitor:
    """
    Real-time console dashboard for NEXORA.
    Displays system status, equity, drawdown, and risk metrics.
    """

    def __init__(self, logger, portfolio=None, risk_manager=None):
        self.logger = logger
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.console = Console()
        self.active = True

    async def display(self, refresh_interval=2):
        """
        Periodically display system stats.
        """
        while self.active:
            self.console.clear()
            table = Table(title="📊 NEXORA Live Dashboard")

            table.add_column("Metric", justify="left", style="bold cyan")
            table.add_column("Value", justify="right", style="bold green")

            # --- Portfolio metrics ---
            if self.portfolio:
                equity = self.portfolio.get_equity()
                drawdown = self.portfolio.get_drawdown()
                table.add_row("Equity", f"${equity:,.2f}")
                table.add_row("Max Drawdown", f"{drawdown:.2f}%")

            # --- Risk state ---
            if self.risk_manager:
                state = getattr(self.risk_manager, "risk_state", "N/A")
                table.add_row("Risk State", state)

            self.console.print(table)

            await asyncio.sleep(refresh_interval)

    def stop(self):
        """Stop the live dashboard."""
        self.active = False
        self.logger.info("🛑 LiveMonitor stopped.")
