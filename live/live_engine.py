import asyncio
import logging
from datetime import datetime

from live.data_feed import KrakenDataFeed
from live.paper_executor import PaperExecutor
from monitoring.live_logger import LiveLogger


class LiveEngine:
    """Central live-trading simulation orchestrator for NEXORA."""

    def __init__(self, config, strategy_cls):
        # Load core config
        self.config = config
        self.strategy_cls = strategy_cls
        self.symbols = config.get("live", {}).get("symbols", ["BTC/USD"])
        self.log_interval = config.get("live", {}).get("log_interval", 5)
        self.snapshot_interval = config.get("live", {}).get("snapshot_interval", 60)

        # Core modules
        self.queue = asyncio.Queue()
        self.executor = PaperExecutor(config)
        self.strategy = strategy_cls(config=config)
        self.feed = KrakenDataFeed(self.symbols, self.queue)
        self.live_logger = LiveLogger()

        # Logging setup
        self.logger = logging.getLogger("LiveEngine")
        self.logger.setLevel(logging.INFO)

        self.last_snapshot = datetime.utcnow()
        self.running = True

    async def start(self):
        """Initialize and start live feed + trading loop."""
        self.logger.info(f"🚀 Starting LiveEngine for {self.symbols}")

        feed_task = asyncio.create_task(self.feed.connect())
        consumer_task = asyncio.create_task(self._consume_data())

        try:
            await asyncio.gather(feed_task, consumer_task)
        except asyncio.CancelledError:
            self.logger.warning("LiveEngine cancelled externally.")
        except Exception as e:
            self.logger.exception(f"Critical error: {e}")
        finally:
            await self.stop()

    async def _consume_data(self):
        """Main event loop: consume ticks, process strategy, execute trades."""
        while self.running:
            try:
                data = await self.queue.get()

                # Pass tick to strategy for signal generation
                signal = self.strategy.run_live(data)
                trade = None

                # Execute trade signal (if any)
                if signal:
                    trade = await self.executor.execute_trade(signal)
                    self.logger.info(f"✅ Executed Trade: {trade}")

                # Periodic metrics update
                snapshot = self.executor.portfolio_snapshot()
                self.live_logger.update(snapshot, last_trade=trade)

                # Periodic snapshot logging
                now = datetime.utcnow()
                if (now - self.last_snapshot).total_seconds() >= self.snapshot_interval:
                    self.logger.info(f"[SNAPSHOT] {snapshot}")
                    self.last_snapshot = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Live loop error: {e}", exc_info=True)
                await asyncio.sleep(2)  # small cooldown to prevent spam loops

    async def stop(self):
        """Gracefully stop all live components."""
        if not self.running:
            return
        self.running = False

        self.logger.info("🧩 Stopping LiveEngine...")
        await self.feed.stop()
        self.executor.export_trades()
        self.logger.info("📘 Live session terminated and trade log exported.")
