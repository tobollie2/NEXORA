import time


class LiveMonitor:
    """
    Simplified logger-based system monitor for NEXORA.
    Replaces Rich visuals with periodic log summaries.
    """

    def __init__(self, logger, portfolio, risk_manager):
        self.logger = logger
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.loop_times = []
        self.latencies = []
        self.last_log_time = time.time()
        self.log_interval = 10  # seconds between log updates

        self.logger.info("📊 LiveMonitor initialized (logging mode only).")

    # --------------------------------------------------------------
    def record_loop_time(self, duration):
        """Record time taken for one strategy loop iteration."""
        self.loop_times.append(duration)
        if len(self.loop_times) > 100:
            self.loop_times.pop(0)

    def update_data_latency(self, latency):
        """Record latency of latest data update."""
        self.latencies.append(latency)
        if len(self.latencies) > 100:
            self.latencies.pop(0)

    # --------------------------------------------------------------
    def log_system_status(self):
        """Log summarized metrics periodically (no visual output)."""
        now = time.time()
        if now - self.last_log_time < self.log_interval:
            return  # only log once every few seconds

        avg_loop = sum(self.loop_times) / len(self.loop_times) if self.loop_times else 0
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0

        equity = getattr(self.portfolio, "current_equity", 1000.0)
        drawdown = getattr(self.portfolio, "max_drawdown", 0.0)
        risk_state = getattr(self.risk_manager, "risk_state", "NORMAL")
        open_positions = getattr(self.portfolio, "open_positions", 0)

        self.logger.info(
            f"📈 Status | Equity=${equity:,.2f} | Drawdown={drawdown:.2%} | "
            f"Risk={risk_state} | Positions={open_positions} | "
            f"Loop={avg_loop:.2f}s | Latency={avg_latency*1000:.1f}ms"
        )

        self.last_log_time = now

    # --------------------------------------------------------------
    def stop(self):
        """Graceful shutdown for monitoring system."""
        self.logger.info("🧹 LiveMonitor stopped gracefully.")
