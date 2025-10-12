import csv
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler

# ------------------------------------------------------------
# LOGGER SETUP
# ------------------------------------------------------------


def setup_logger(
    name="NEXORA", log_path=None, log_level="INFO", max_bytes=2_000_000, backup_count=5
):
    """
    Creates and configures a rich-enhanced logger with file rotation.

    Args:
        name (str): Name of the logger instance.
        log_path (str): Path to save the log file.
        log_level (str): Logging level ("DEBUG", "INFO", etc.).
        max_bytes (int): Max file size before rotating (default ~2MB).
        backup_count (int): Number of backup files to keep.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        # Rich console handler
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=False,
            show_level=True,
            show_path=False,
            console=Console(),
        )
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.addHandler(console_handler)

        # File logging (rotating)
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            logger.addHandler(file_handler)

        logger.info(f"🧠 NEXORA Logger initialized.")
        if log_path:
            logger.info(f"🗂️ Log file path: {log_path}")

    return logger


# ------------------------------------------------------------
# TRADE LOGGING UTILITIES
# ------------------------------------------------------------


def log_trade(
    timestamp, symbol, side, qty, price, pnl=0.0, equity=0.0, csv_path="logs/trade_log.csv"
):
    """
    Records trade data to a CSV file (append mode).

    Args:
        timestamp (str): UTC timestamp of trade.
        symbol (str): Trading pair (e.g., BTC/USD).
        side (str): "BUY" or "SELL".
        qty (float): Quantity traded.
        price (float): Trade price.
        pnl (float): Profit/loss from trade.
        equity (float): Current portfolio equity.
        csv_path (str): Path to CSV trade log.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "symbol", "side", "qty", "price", "pnl", "equity"])
        writer.writerow([timestamp, symbol, side, qty, price, pnl, equity])


# ------------------------------------------------------------
# QUICK TEST (Optional standalone test)
# ------------------------------------------------------------
if __name__ == "__main__":
    logger = setup_logger("TEST_LOGGER", "logs/test_logger.log", "DEBUG")
    logger.info("Logger test successful.")
    log_trade(datetime.utcnow().isoformat(), "BTC/USD", "BUY", 0.1, 64000, 25.5, 1025.5)
    logger.info("Trade logging test successful.")
