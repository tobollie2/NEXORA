import asyncio
import os

from statistical_arbitrage import StatisticalArbitrageStrategy

from config.settings_loader import load_settings
from data.ingestion import DataIngestion
from monitoring.live_monitor import LiveMonitor
from monitoring.logging_utils import setup_logger
from portfolio.allocator import PortfolioAllocator
from portfolio.trade_logger import TradeLogger  # <-- NEW: Trade Logging
from risk.risk_manager import RiskManager
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend import TrendFollowingStrategy
from tools.log_analyzer import NEXORAAnalyzer  # <-- Auto post-run analysis


class NEXORA:
    """
    Main NEXORA Trading Engine.
    Handles configuration loading, backtest execution, trade logging,
    risk evaluation, and post-run analytics.
    """

    def __init__(self, config_path="config/settings.yaml"):
        # --- Load Configuration ---
        self.config = load_settings(config_path)

        # --- Setup Logging ---
        log_path = self.config["system"].get("log_path", "logs/nexora.log")
        log_level = self.config["system"].get("log_level", "INFO")
        self.logger = setup_logger("NEXORA", log_path, log_level)
        self.logger.info("🧠 NEXORA Logger initialized.")
        self.logger.info(f"🪶 Log file path: {log_path}")

        # --- Data Feed ---
        self.data_mode = self.config["data"]["source"].upper()
        self.symbols = self.config["data"].get("symbols", ["BTC/USD"])
        self.buffer_size = self.config["data"].get("buffer_size", 500)
        self.data_feed = DataIngestion(
            mode=self.data_mode,
            symbols=self.symbols,
            buffer_size=self.buffer_size,
            logger=self.logger,
        )

        self.logger.info(
            f"📊 DataIngestion initialized in {self.data_mode} mode for symbols: "
            f"{', '.join(self.symbols)} | Buffer size={self.buffer_size}"
        )

        # --- Portfolio & Risk Systems ---
        self.portfolio = PortfolioAllocator(self.logger, self.config["system"])
        self.risk_manager = RiskManager(self.logger, self.config["risk"])

        # --- Live Monitor (console metrics only) ---
        self.monitor = LiveMonitor(self.logger, self.portfolio, self.risk_manager)
        self.logger.info("🖥️ Live monitoring initialized successfully.")

        # --- Trade Logging ---
        self.trade_logger = TradeLogger()
        self.logger.info("📜 Trade logging initialized successfully.")

        # --- Strategies ---
        self.strategies = {
            "trend": TrendFollowingStrategy(
                self.config["strategy"]["trend_following"], self.logger
            ),
            "mean": MeanReversionStrategy(self.config["strategy"]["mean_reversion"], self.logger),
            "stat_arb": StatisticalArbitrageStrategy(
                self.config["strategy"].get("stat_arb", {}), self.logger
            ),
        }
        self.logger.info("✅ Core systems initialized successfully.")

        # --- System Refresh Rate ---
        self.refresh_rate = self.config["system"].get("refresh_rate", 2)

    # -----------------------------------------------------------------
    async def run(self):
        """Main asynchronous execution loop for backtesting."""
        self.logger.info("🚀 Starting main NEXORA loop...")

        try:
            while True:
                loop_start = asyncio.get_event_loop().time()

                # --- Fetch or Simulate Market Data ---
                market_data = await self.data_feed.get_latest_data()

                # --- Process Active Strategies ---
                for name, strategy in self.strategies.items():
                    try:
                        signal = strategy.generate_signal(market_data)

                        if isinstance(signal, dict) and "price" in signal:
                            self.logger.info(f"📈 {name.upper()} → {signal}")

                            # --- Simulate trade execution and record trade ---
                            trade_quantity = 1.0  # Placeholder (can be dynamically calculated)
                            pnl = self.portfolio.allocate_capital(signal, signal["price"])
                            self.risk_manager.evaluate_risk(self.portfolio)

                            # --- Record Trade Event ---
                            self.trade_logger.record_trade(
                                strategy=name.upper(),
                                symbol=signal.get("symbol", self.symbols[0]),
                                signal=signal.get("signal", "UNKNOWN"),
                                price=signal["price"],
                                quantity=trade_quantity,
                                pnl=pnl if pnl is not None else 0.0,
                                equity=self.portfolio.current_equity,
                            )

                        else:
                            self.logger.debug(f"🕒 {name.upper()} → HOLD / No signal")

                    except Exception as e:
                        self.logger.error(f"❌ Error in {name} strategy: {e}")

                # --- Measure and Record Loop Time ---
                loop_end = asyncio.get_event_loop().time()
                loop_time = loop_end - loop_start
                self.monitor.record_loop_time(loop_time)

                # --- Update Live Logging Status ---
                self.logger.info(
                    f"📊 Status | Equity=${self.portfolio.current_equity:,.2f} | "
                    f"Drawdown={self.portfolio.max_drawdown:.3f} | "
                    f"Risk={self.risk_manager.risk_state} | "
                    f"Positions={self.portfolio.open_positions} | "
                    f"Loop={loop_time:.2f}s"
                )

                await asyncio.sleep(self.refresh_rate)

        except KeyboardInterrupt:
            self.logger.info("🛑 NEXORA stopped by user.")
        except Exception as e:
            self.logger.error(f"🚨 Fatal error in main loop: {e}")

        # -----------------------------------------------------------------
        finally:
            self.logger.info("💾 Saving final portfolio and logs...")

            # --- Trade Summary Output ---
            trade_summary = self.trade_logger.summarize()
            self.logger.info(
                f"🧾 Trade Summary | Total Trades={trade_summary['total_trades']} | "
                f"Win Rate={trade_summary['win_rate']}% | "
                f"Total PnL=${trade_summary['total_pnl']:.2f}"
            )

            # --- Run Log Analyzer ---
            try:
                self.logger.info("📊 Running post-run analysis...")
                analyzer = NEXORAAnalyzer()
                if analyzer.load_backtest_summary():
                    analyzer.summarize_results()
                    analyzer.plot_comparisons()
                else:
                    self.logger.warning("⚠️ No backtest summaries found for analysis.")
            except Exception as e:
                self.logger.error(f"⚠️ Post-run analysis failed: {e}")

            # --- Cleanup ---
            self.monitor.stop()
            self.logger.info("🧹 NEXORA session closed gracefully.")


# -----------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")

    nexora = NEXORA()
    asyncio.run(nexora.run())
