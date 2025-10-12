# /live/paper_executor.py
import asyncio
import logging
from datetime import datetime


class PaperExecutor:
    """Simulated trade executor that applies latency, slippage, and fees."""

    def __init__(self, config):
        live_cfg = config.get("live", {})
        self.latency_ms = live_cfg.get("latency_ms", 100)
        self.slippage_bps = live_cfg.get("slippage_bps", 5)
        self.fee_bps = live_cfg.get("fee_bps", 2)
        self.balance = config.get("portfolio", {}).get("initial_balance", 100_000.0)

        self.positions = {}  # {symbol: {"size": float, "avg_price": float}}
        self.trade_log = []
        self.logger = logging.getLogger("PaperExecutor")
        self.logger.setLevel(logging.INFO)

    async def execute_trade(self, signal: dict):
        """Executes a trade signal with simulated latency."""
        symbol = signal["symbol"]
        side = signal["side"].upper()
        size = float(signal["size"])
        price = float(signal["price"])

        await asyncio.sleep(self.latency_ms / 1000)

        slip_mult = 1 + (self.slippage_bps / 10_000) * (1 if side == "BUY" else -1)
        executed_price = price * slip_mult
        cost = executed_price * size
        fee = cost * (self.fee_bps / 10_000)

        # Update portfolio
        self._update_position(symbol, side, size, executed_price, fee)

        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "side": side,
            "size": size,
            "executed_price": round(executed_price, 4),
            "fee": round(fee, 4),
            "balance": round(self.balance, 2),
        }
        self.trade_log.append(trade)

        self.logger.info(
            f"{side} {size} {symbol} @ {executed_price:.2f} "
            f"(fee {fee:.2f}, bal {self.balance:.2f})"
        )
        return trade

    def _update_position(self, symbol, side, size, executed_price, fee):
        pos = self.positions.get(symbol, {"size": 0.0, "avg_price": 0.0})
        prev_size = pos["size"]
        prev_price = pos["avg_price"]

        if side == "BUY":
            new_size = prev_size + size
            new_price = (
                (prev_price * prev_size + executed_price * size) / new_size
                if new_size != 0
                else executed_price
            )
            pos["size"] = new_size
            pos["avg_price"] = new_price
            self.balance -= executed_price * size + fee

        elif side == "SELL":
            new_size = prev_size - size
            pnl = (executed_price - prev_price) * min(size, prev_size)
            self.balance += executed_price * size - fee + pnl
            pos["size"] = new_size
            if new_size <= 0:
                pos["avg_price"] = 0.0  # Flat position

        self.positions[symbol] = pos

    def portfolio_snapshot(self):
        """Return current portfolio state."""
        unrealized_pnl = 0.0
        for symbol, pos in self.positions.items():
            unrealized_pnl += pos["size"] * pos["avg_price"]  # Approximation
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "balance": round(self.balance, 2),
            "positions": self.positions,
            "unrealized_pnl": round(unrealized_pnl, 2),
        }

    def export_trades(self, path="reports/live_trades.csv"):
        import pandas as pd

        if not self.trade_log:
            return
        pd.DataFrame(self.trade_log).to_csv(path, index=False)
        self.logger.info(f"Trade log exported → {path}")
