import pandas as pd
from datetime import datetime
from monitoring.logging_utils import log_trade


class PortfolioAllocator:
    """
    Tracks positions, equity, and realized/unrealized PnL.
    Handles position sizing, capital allocation, and equity updates.
    """

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

        self.initial_capital = config.get("initial_capital", 1000.0)
        self.current_capital = self.initial_capital
        self.cash = self.initial_capital
        self.positions = {}  # {symbol: {"side": 1/-1, "qty": float, "entry_price": float}}
        self.trade_history = []
        self.equity_curve = []

        # Drawdown tracking
        self.equity_high = self.initial_capital
        self.max_drawdown = 0.0

        self.logger.info(
            f"💰 PortfolioAllocator initialized | Starting capital ${self.initial_capital:,.2f}"
        )

    # -------------------------------------------------------------------------
    def allocate_capital(self, trade, price):
        """Allocate or free capital based on trade execution."""
        symbol = trade["symbol"]
        side = 1 if trade["side"] == "BUY" else -1
        qty = trade.get("qty", 1.0)
        trade_value = qty * price

        # Ensure position exists
        if symbol not in self.positions:
            self.positions[symbol] = {"side": side, "qty": qty, "entry_price": price}
            self.cash -= trade_value
            pnl = 0.0
        else:
            pos = self.positions[symbol]

            # Same direction — scale in
            if pos["side"] == side:
                new_qty = pos["qty"] + qty
                pos["entry_price"] = (
                    (pos["entry_price"] * pos["qty"]) + (price * qty)
                ) / new_qty
                pos["qty"] = new_qty
                self.cash -= trade_value
                pnl = 0.0

            # Opposite direction — scale out or close
            else:
                closed_qty = min(pos["qty"], qty)
                pnl = closed_qty * (price - pos["entry_price"]) * pos["side"]
                self.cash += trade_value + pnl
                pos["qty"] -= closed_qty

                # If fully closed, remove position
                if pos["qty"] <= 0:
                    del self.positions[symbol]

        # Update equity + log trade
        self._update_equity()
        self._record_trade(trade, pnl)

    # -------------------------------------------------------------------------
    def _record_trade(self, trade, pnl=0.0):
        """Record trade and persist to CSV."""
        trade_record = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": trade["symbol"],
            "side": trade["side"],
            "qty": trade.get("qty", 1.0),
            "price": trade["price"],
            "pnl": round(pnl, 2),
            "equity": round(self.current_capital, 2),
        }
        self.trade_history.append(trade_record)

        log_trade(
            timestamp=trade_record["timestamp"],
            symbol=trade_record["symbol"],
            side=trade_record["side"],
            qty=trade_record["qty"],
            price=trade_record["price"],
            pnl=trade_record["pnl"],
            equity=trade_record["equity"],
        )

        self.logger.info(
            f"💹 Trade logged: {trade_record['side']} {trade_record['qty']} {trade_record['symbol']} "
            f"@ {trade_record['price']} | PnL={trade_record['pnl']:.2f} | Equity={trade_record['equity']:.2f}"
        )

    # -------------------------------------------------------------------------
    def _update_equity(self):
        """Recalculate portfolio equity and drawdown."""
        open_pnl = 0.0
        for sym, pos in self.positions.items():
            open_pnl += (pos["entry_price"] * pos["qty"]) * pos["side"]

        self.current_capital = self.cash + open_pnl
        self.equity_curve.append(self.current_capital)

        if self.current_capital > self.equity_high:
            self.equity_high = self.current_capital

        drawdown = 1 - (self.current_capital / self.equity_high)
        self.max_drawdown = max(self.max_drawdown, drawdown)

        self.logger.info(
            f"📊 Equity={self.current_capital:.2f} | Drawdown={drawdown * 100:.2f}% | MaxDD={self.max_drawdown * 100:.2f}%"
        )

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
    def get_equity(self):
        return round(self.current_capital, 2)

    def get_drawdown(self):
        return round(self.max_drawdown * 100, 2)

    def get_positions(self):
        return self.positions

    def get_equity_series(self):
        return pd.DataFrame(
            {"timestamp": range(len(self.equity_curve)), "equity": self.equity_curve}
        )
