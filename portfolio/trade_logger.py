import os
import csv
from datetime import datetime


class TradeLogger:
    """
    Central trade logging system for NEXORA.
    Records all executed trades with metadata for post-analysis.
    """

    def __init__(self, log_dir="logs"):
        self.trade_log_path = os.path.join(log_dir, "trades.csv")

        # Ensure directory and CSV header exist
        os.makedirs(log_dir, exist_ok=True)
        if not os.path.exists(self.trade_log_path):
            with open(self.trade_log_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "timestamp",
                    "strategy",
                    "symbol",
                    "signal",
                    "price",
                    "quantity",
                    "pnl",
                    "equity"
                ])

    def record_trade(self, strategy, symbol, signal, price, quantity, pnl, equity):
        """Write a new trade entry to the CSV log."""
        with open(self.trade_log_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                strategy,
                symbol,
                signal,
                f"{price:.2f}",
                f"{quantity:.4f}",
                f"{pnl:.2f}",
                f"{equity:.2f}"
            ])

    def summarize(self):
        """Generate summary statistics from the trade log."""
        if not os.path.exists(self.trade_log_path):
            return {"total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0}

        with open(self.trade_log_path, mode="r") as file:
            reader = csv.DictReader(file)
            trades = list(reader)

        total_trades = len(trades)
        total_pnl = sum(float(t["pnl"]) for t in trades)
        wins = sum(1 for t in trades if float(t["pnl"]) > 0)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
        }
