import random
import time
from datetime import datetime

from monitoring.logging_utils import log_trade


class OrderManager:
    """
    Simulated order execution engine for NEXORA.
    Models latency, slippage, and trade confirmation.
    """

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

        self.latency = config.get("execution", {}).get("latency", 0.5)  # seconds
        self.slippage = config.get("execution", {}).get("slippage", 0.0005)  # 0.05%
        self.min_order_size = config.get("execution", {}).get("min_order_size", 1.0)
        self.order_id = 0

    def execute_trade(self, signal, position_size, current_price):
        """
        Simulate execution of a buy/sell order.
        Adds random slippage and delay to mimic live market fills.
        """
        if position_size < self.min_order_size:
            self.logger.warning("❗ Order size below minimum, skipped execution.")
            return None

        # Simulated execution latency
        exec_delay = random.uniform(0, self.latency)
        time.sleep(exec_delay)

        # Direction: +1 = long (buy), -1 = short (sell)
        side = 1 if signal > 0 else -1
        trade_side = "BUY" if side > 0 else "SELL"

        # Apply slippage
        price_adj = current_price * (1 + side * random.uniform(-self.slippage, self.slippage))
        self.order_id += 1

        trade = {
            "order_id": self.order_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "side": trade_side,
            "qty": position_size,
            "price": round(price_adj, 2),
            "symbol": "SIMUSD",
            "status": "filled",
        }

        self.logger.info(
            f"⚙️ Order {self.order_id} | {trade_side} {position_size} @ {price_adj:.2f} "
            f"(slip={self.slippage*100:.2f}% | delay={exec_delay:.2f}s)"
        )

        # Log to trades.csv
        log_trade(
            timestamp=trade["timestamp"],
            symbol=trade["symbol"],
            side=trade_side,
            qty=trade["qty"],
            price=trade["price"],
            pnl=0.0,
            equity=0.0,
        )

        return trade
